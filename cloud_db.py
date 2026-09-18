"""PostgreSQL exclusivo do piloto. Nenhum acesso ao SQLite local."""
from functools import lru_cache
import os
from pathlib import Path

import bcrypt
import pandas as pd
import psycopg
from psycopg.conninfo import conninfo_to_dict
import sqlglot
from sqlglot import exp
import streamlit as st

SCHEMA = 'estoque_teste'


def setting(name):
    value = os.environ.get(name)
    if value is not None:
        return value
    try:
        return str(st.secrets.get(name, ''))
    except FileNotFoundError:
        return ''


def raw_connection():
    url = setting('TEST_DATABASE_URL')
    if not url:
        raise ValueError('Configure TEST_DATABASE_URL nos Secrets do ambiente de teste.')
    # Nao aceitar opcoes que mudem o schema ou uma conexao SQLite.
    config = conninfo_to_dict(url)
    config.pop('options', None)
    config.update(sslmode='require', connect_timeout='10', application_name='estoque_teste')
    raw = psycopg.connect(**config, prepare_threshold=None)
    raw.execute('SET search_path TO estoque_teste')
    raw.commit()
    return raw


@lru_cache(maxsize=512)
def compile_query(query):
    """Converte o SQL legado parametrizado, sem interpolar valores do usuario."""
    parsed = sqlglot.parse(query, read='sqlite')
    if len(parsed) != 1 or parsed[0] is None:
        raise ValueError('Execute uma instrucao SQL por vez.')
    tree = parsed[0]
    aliases = {a.alias for a in tree.find_all(exp.Alias)}
    for a in tree.find_all(exp.Alias):
        a.set('alias', exp.to_identifier(a.alias, quoted=True))
    for column in tree.find_all(exp.Column):
        if not column.table and column.name in aliases:
            column.set('this', exp.to_identifier(column.name, quoted=True))
    for like in list(tree.find_all(exp.Like)):
        like.replace(exp.ILike(this=like.this.copy(), expression=like.expression.copy()))
    for placeholder in list(tree.find_all(exp.Placeholder)):
        placeholder.replace(exp.Var(this='__ESTOQUE_PARAM__'))
    inserted_id = isinstance(tree, exp.Insert) and not tree.args.get('returning')
    if inserted_id:
        tree.set('returning', exp.Returning(expressions=[exp.column('id')]))
    sql = tree.sql(dialect='postgres', unsupported_level=sqlglot.ErrorLevel.RAISE)
    # Psycopg interpreta % mesmo em literais quando recebe parametros.
    sql = sql.replace('%', '%%').replace('__ESTOQUE_PARAM__', '%s')
    return sql, inserted_id


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.raw = connection.raw.cursor()
        self.lastrowid = None

    def execute(self, query, params=None):
        if query.strip().upper() == 'BEGIN IMMEDIATE':
            # PostgreSQL protege as baixas por UPDATE condicional e bloqueio de linha.
            self.connection.raw.execute('SELECT 1')
            return self
        sql, inserted_id = compile_query(query)
        raw = self.connection.raw
        raw.execute('SAVEPOINT estoque_statement')
        try:
            self.raw.execute(sql, tuple(params) if params is not None else ())
            self.lastrowid = None
            if inserted_id:
                row = self.raw.fetchone()
                self.lastrowid = row[0] if row else None
        except Exception:
            raw.execute('ROLLBACK TO SAVEPOINT estoque_statement')
            raw.execute('RELEASE SAVEPOINT estoque_statement')
            raise
        raw.execute('RELEASE SAVEPOINT estoque_statement')
        return self

    @property
    def rowcount(self):
        return self.raw.rowcount

    @property
    def description(self):
        return self.raw.description

    def fetchone(self):
        return self.raw.fetchone()

    def fetchall(self):
        return self.raw.fetchall()

    def close(self):
        self.raw.close()

    def __iter__(self):
        return iter(self.raw)


class Connection:
    def __init__(self, raw):
        self.raw = raw

    def cursor(self):
        return Cursor(self)

    def execute(self, query, params=None):
        return self.cursor().execute(query, params)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()


def get_conn():
    return Connection(raw_connection())


def read_sql_query(query, conn, params=None):
    cursor = conn.execute(query, params)
    try:
        return pd.DataFrame.from_records(cursor.fetchall(), columns=[c.name for c in cursor.description])
    finally:
        cursor.close()


@st.cache_resource(show_spinner=False)
def initialize():
    """Cria apenas o schema de teste; nao importa dados de producao."""
    password = setting('TEST_ADMIN_PASSWORD')
    if len(password) < 12 or len(password.encode('utf-8')) > 72 or password.startswith('SUBSTITUA_'):
        raise ValueError('Defina TEST_ADMIN_PASSWORD com pelo menos 12 caracteres e ate 72 bytes.')
    raw = raw_connection()
    try:
        raw.execute('SELECT pg_advisory_xact_lock(18092026)')
        schema_sql = Path(__file__).with_name('schema.sql').read_text(encoding='utf-8')
        for statement in schema_sql.split(';'):
            if statement.strip():
                raw.execute(statement)
        raw.execute('INSERT INTO seq_recibo(id,valor) VALUES(1,2002) ON CONFLICT(id) DO NOTHING')
        if not raw.execute('SELECT 1 FROM usuarios LIMIT 1').fetchone():
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            raw.execute('INSERT INTO usuarios(usuario,senha,perfil) VALUES(%s,%s,%s)',
                        ('admin_teste', password_hash, 'Administrador'))
        raw.commit()
    finally:
        raw.close()


def save_setting(key, value):
    with raw_connection() as raw:
        raw.execute('INSERT INTO configuracoes_teste(chave,valor) VALUES(%s,%s) '
                    'ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor', (key, value))


def load_setting(key):
    with raw_connection() as raw:
        row = raw.execute('SELECT valor FROM configuracoes_teste WHERE chave=%s', (key,)).fetchone()
        return row[0] if row else None
