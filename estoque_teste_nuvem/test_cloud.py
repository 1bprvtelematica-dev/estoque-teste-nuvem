"""Testes locais sem ler ou modificar o estoque instalado."""
import ast
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from cloud_db import compile_query, Cursor, Connection

ROOT = Path(__file__).resolve().parent


class SQLTests(unittest.TestCase):
    def test_parameters_remain_bound_and_percent_is_escaped(self):
        sql, _ = compile_query("SELECT nome FROM materiais WHERE nome LIKE ? AND nome <> '100% ?'")
        self.assertIn('ILIKE %s', sql)
        self.assertIn("'100%% ?'", sql)

    def test_aliases_preserve_dataframe_column_names(self):
        sql, _ = compile_query("SELECT nome 'Material', COUNT(*) AS QtdAtual FROM materiais GROUP BY nome ORDER BY Material")
        self.assertIn('AS "Material"', sql)
        self.assertIn('AS "QtdAtual"', sql)
        self.assertIn('ORDER BY "Material"', sql)

    def test_distinct_identifiers_and_inserted_id(self):
        sql, _ = compile_query('SELECT GROUP_CONCAT(DISTINCT num_recibo) FROM historico')
        self.assertIn('STRING_AGG(DISTINCT num_recibo', sql)
        sql, returns_id = compile_query('INSERT INTO materiais(nome,quantidade) VALUES(?,?)')
        self.assertTrue(returns_id)
        self.assertTrue(sql.endswith('RETURNING id'))

    def test_all_literal_queries_in_application(self):
        tree = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))
        count = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = getattr(node.func, 'attr', getattr(node.func, 'id', ''))
            first = node.args[0]
            if name not in ('execute', 'read_sql_query') or not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                continue
            if first.value == 'BEGIN IMMEDIATE':
                continue
            with self.subTest(line=node.lineno):
                compile_query(first.value)
            count += 1
        self.assertGreater(count, 65)

    def test_no_local_database_fallback(self):
        source = (ROOT / 'app.py').read_text(encoding='utf-8')
        self.assertNotIn('sqlite3', source)
        self.assertNotIn('DB_PATH', source)
        self.assertNotIn('admin123', source)

    def test_source_program_unchanged(self):
        original = ROOT.parent / 'appv7.1.py'
        if not original.exists():
            self.skipTest('Verificacao aplicavel somente ao workspace original.')
        expected = (ROOT / 'ORIGEM.sha256').read_text().split()[0]
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), expected)

    def test_missing_configuration_displays_setup_without_database(self):
        from streamlit.testing.v1 import AppTest
        with patch('cloud_db.setting', return_value=''):
            app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        self.assertFalse(list(app.exception))
        self.assertTrue(any('Configure o banco' in message.value for message in app.info))


@unittest.skipUnless(os.environ.get('TEST_DATABASE_URL'), 'Requer PostgreSQL de teste configurado.')
class PostgreSQLIntegrationTests(unittest.TestCase):
    def test_rollback_uniqueness_reports_and_sequence(self):
        import cloud_db
        import psycopg
        import uuid
        cloud_db.initialize()
        conn = cloud_db.get_conn()
        name = 'TESTE_' + uuid.uuid4().hex
        try:
            cur = conn.execute('INSERT INTO materiais(nome,quantidade,patrimonio,entrada_registrada) VALUES(?,?,?,?)', (name, 2, name, 1))
            item_id = cur.lastrowid
            self.assertIsInstance(item_id, int)
            # Falha recuperavel nao deve invalidar a transacao inteira.
            with self.assertRaises(psycopg.IntegrityError):
                conn.execute('INSERT INTO materiais(nome,patrimonio) VALUES(?,?)', (name, name))
            changed = conn.execute('UPDATE materiais SET quantidade=quantidade-? WHERE id=? AND quantidade>=?', (1, item_id, 1))
            self.assertEqual(changed.rowcount, 1)
            failed = conn.execute('UPDATE materiais SET quantidade=quantidade-? WHERE id=? AND quantidade>=?', (5, item_id, 5))
            self.assertEqual(failed.rowcount, 0)
            df = cloud_db.read_sql_query("SELECT nome 'Material',quantidade 'Qtd' FROM materiais WHERE id=?", conn, (item_id,))
            self.assertEqual(list(df.columns), ['Material', 'Qtd'])
            self.assertEqual(int(df.iloc[0]['Qtd']), 1)
            conn.execute('UPDATE seq_recibo SET valor=valor+1 WHERE id=1')
            conn.rollback()
            self.assertIsNone(conn.execute('SELECT id FROM materiais WHERE nome=?', (name,)).fetchone())
        finally:
            conn.rollback()
            conn.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
