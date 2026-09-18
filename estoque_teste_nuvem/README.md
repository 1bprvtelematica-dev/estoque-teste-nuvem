# Estoque — cópia de teste em nuvem

Esta pasta contém uma cópia independente da aplicação, adaptada para
Streamlit Community Cloud + PostgreSQL no Supabase. **Ainda não publicada.**
O programa instalado em `C:\estoque\appv7.1.py`, seu banco `estoque.db`,
seus serviços e suas configurações não são usados nem alterados por esta cópia.

O teste começa vazio, com um administrador exclusivo. Cadastre dados fictícios
para testar materiais, fornecedores, clientes, entradas, saídas e recibos.
Não há sincronização com o estoque real nem importação automática de seus dados.

## O que foi adaptado

- Conexão PostgreSQL com TLS, exclusivamente via `TEST_DATABASE_URL`.
- Schema separado `estoque_teste`, fora do schema público da API Supabase.
- Consultas parametrizadas, pesquisas sem diferenciar maiúsculas/minúsculas,
  agrupamentos, nomes de colunas dos relatórios e identificação de itens inseridos.
- Transações de estoque preservadas; a sequência de recibos usa bloqueio de linha.
- Cadastro inicial `admin_teste`, com senha exclusiva definida nos Secrets.
- Imagem personalizada de recibo persistida no PostgreSQL.
- Backup de SQLite/pasta de rede substituído por orientação de backup PostgreSQL.
  **Não existe backup automático neste piloto.**
- A exclusão de registros não reinicia os IDs internos do PostgreSQL.

## Contas necessárias

1. GitHub: um repositório **privado e novo**, por exemplo `estoque-teste-nuvem`.
2. Supabase: projeto **novo, no plano Free e exclusivo para este teste**.
3. Streamlit Community Cloud: acesso ao repositório de teste no GitHub.

Não é necessário contratar domínio; o Streamlit fornece endereço HTTPS
`nome-escolhido.streamlit.app`, conforme disponibilidade.
Não envie senhas no chat nem coloque credenciais no GitHub.

## Preparar o Supabase

1. Crie o projeto de teste no plano Free e guarde a senha do banco.
2. Em **Connect**, selecione **Session pooler**, porta **5432**, compatível com IPv4.
3. Copie a URI PostgreSQL e substitua o marcador de senha pela senha do projeto.
   Caracteres especiais da senha devem ser codificados para URL.
4. Guarde a URI para os Secrets do Streamlit. Não use a chave anon/API como senha.
5. O primeiro início cria apenas as tabelas do schema `estoque_teste` e os índices.
   Não adicione esse schema aos schemas expostos pela Data API.
   A conexão administrativa fica somente no servidor Streamlit.

## Enviar a cópia para o GitHub

Envie os arquivos **de dentro desta pasta**, na raiz do repositório novo:

- `app.py`, `cloud_db.py`, `schema.sql`, `requirements.txt`;
- `.streamlit/config.toml` e `.gitignore`;
- imagens desta pasta, `README.md`, `test_cloud.py` e `secrets.example.toml`.

**Não envie a pasta `C:\estoque` inteira.** Não envie `.venv`, bancos `.db`,
logs, backups, `.streamlit/secrets.toml` ou o gerador `preparar_copia.py`.
O arquivo ZIP de publicação preparado ao lado desta pasta inclui somente
os arquivos necessários, sem banco e sem credenciais.

## Publicar no Streamlit Community Cloud

1. Crie uma aplicação a partir do repositório novo.
2. Selecione `app.py` como arquivo principal e **Python 3.13**.
3. Em **Advanced settings / Secrets**, adicione:

```toml
TEST_DATABASE_URL = "URI_DO_SESSION_POOLER_DO_PROJETO_DE_TESTE"
TEST_ADMIN_PASSWORD = "SUA_SENHA_FORTE_EXCLUSIVA_COM_12_OU_MAIS_CARACTERES"
```

4. Publique e mantenha o acesso da aplicação privado para os participantes do teste.
5. Entre no sistema com `admin_teste` e a senha definida acima.

A senha inicial só é usada quando não existe usuário no banco de teste.
Mudar o Secret depois não redefine a senha de um usuário existente.
Use a tela de usuários para alterar a senha.
Sem os Secrets, a aplicação mostra uma orientação e para; não cria SQLite local.

## Validação antes de convidar as filiais

1. Cadastre fornecedor e cliente fictícios, órgão e material de teste.
2. Registre entrada de 5 unidades; faça saída de 2 e confira saldo 3 e recibo.
3. Teste item individual com patrimônio e tente repetir seu identificador.
4. Consulte histórico, dashboard, busca, relatórios Excel/PDF e reemita o recibo.
5. Teste devolução, edição do recibo, alteração de senha e usuário padrão.
6. Feche e abra o aplicativo; reinicie-o no painel Streamlit e confirme persistência.
7. Com duas sessões, tente retirar simultaneamente a última unidade:
   apenas uma saída deve concluir, sem saldo negativo ou recibo duplicado.
8. Exporte um backup e teste a restauração em outro banco descartável.

Essas etapas com PostgreSQL real ainda precisam ser executadas.

## Testes locais

O ambiente `.venv` desta pasta é separado do Python do sistema instalado.
No PowerShell, a partir desta pasta:

```powershell
.venv\Scripts\python.exe -m unittest test_cloud -v
.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8503
```

Para conectar localmente, salve os Secrets em `.streamlit/secrets.toml` nesta
pasta. Para o teste de integração automatizado, forneça `TEST_DATABASE_URL` e
`TEST_ADMIN_PASSWORD` como variáveis de ambiente no terminal local. Não grave
esses valores em scripts versionados. O teste insere dados fictícios e desfaz
a transação; a inicialização cria o schema e o administrador se necessário.

## Backup e limites

O plano gratuito do Supabase exige uma rotina própria de exportação.
Use ferramentas PostgreSQL compatíveis com a versão do servidor. Configure
`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSSLMODE=require` e um arquivo
de senhas protegido (`PGPASSFILE`), então exporte:

```text
pg_dump --schema=estoque_teste --format=custom --file=estoque_teste.dump
```

Mantenha a exportação fora da hospedagem. A restauração deve ser testada em
outro projeto descartável, nunca no banco local instalado.
O Streamlit pode hibernar sem tráfego e o Supabase Free pode pausar por
inatividade. Esta cópia serve para avaliar o funcionamento, não promete
disponibilidade contínua nem substitui o estoque oficial.

## Referências

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://supabase.com/docs/guides/platform/backups
