# Migração SQLite → PostgreSQL/Supabase - Resumo

## ✅ Alterações Concluídas

### 1. Dependências Atualizadas (`requirements.txt`)
- ✅ Adicionado `psycopg2-binary==2.9.9`

### 2. Código Principal (`main.py`)

#### Imports e Configuração
- ✅ Removido `import sqlite3`
- ✅ Adicionado `import psycopg2` e `psycopg2.extras`
- ✅ Adicionado `psycopg2.pool` para connection pooling
- ✅ Removido `DB_PATH`, adicionado `db_pool` global

#### Funções de Banco
- ✅ `get_db()`: Agora usa connection pool em vez de sqlite
- ✅ `close_db()`: Devolve conexão ao pool (`putconn`)
- ✅ `init_db()`: Schema PostgreSQL com `SERIAL PRIMARY KEY`
- ✅ `ensure_admin()`: Queries com `%s` placeholders
- ✅ Nova função `init_app()`: Inicializa pool e valida `DATABASE_URL`

#### Routes Atualizadas (todas as queries `?` → `%s`)
- ✅ `load_user()`: Query com cursor context
- ✅ `login()`: Query PostgreSQL
- ✅ `signup()`: Query + tratamento `psycopg2.IntegrityError` + rollback
- ✅ `google_callback()`: Múltiplas queries atualizadas
- ✅ `profile_create()`: UPDATE com placeholders PostgreSQL
- ✅ `dashboard()`: INSERT/SELECT com cursor e rollback

### 3. Arquivos de Configuração

#### `.env.example`
- ✅ Template com DATABASE_URL Supabase
- ✅ Documentação inline de onde obter credenciais

#### `SUPABASE_SETUP.md`
- ✅ Guia completo de configuração Supabase
- ✅ Instruções de deploy
- ✅ Troubleshooting
- ✅ Comparação SQLite vs PostgreSQL

#### `.gitignore`
- ✅ Já contém `.env` (nada a fazer)

## 📋 Checklist de Deploy

### Antes de Subir
- [ ] Criar projeto no Supabase
- [ ] Copiar DATABASE_URL do Supabase
- [ ] Gerar SECRET_KEY seguro (`openssl rand -hex 32`)
- [ ] Definir ADMIN_PASS seguro
- [ ] Testar localmente com `.env`

### Deploy na Insights
- [ ] Configurar variáveis de ambiente:
  - `DATABASE_URL` (obrigatória)
  - `SECRET_KEY` (obrigatória)
  - `ADMIN_USER` (opcional)
  - `ADMIN_PASS` (obrigatória em prod)
  - `GOOGLE_CLIENT_ID` (se OAuth)
- [ ] Comando start: `gunicorn main:app --bind 0.0.0.0:$PORT`
- [ ] Verificar health endpoint: `/health`
- [ ] Fazer login com admin e testar criação de usuário

## 🔄 Próximos Passos (quando tiver info da Insights)

1. **Domínio/DNS**: Configurar apontamento do domínio
2. **HTTPS**: Ativar SSL/TLS (atualizar `SESSION_COOKIE_SECURE = True`)
3. **OAuth Redirect URI**: Atualizar no Google Console com domínio final
4. **Backup**: Configurar backups automáticos no Supabase (já incluso no plano gratuito)
5. **Monitoring**: Configurar logs e alertas

## 🧪 Como Testar Localmente

1. Criar `.env` baseado em `.env.example`
2. Configurar DATABASE_URL do Supabase
3. Instalar deps: `pip install -r requirements.txt`
4. Rodar: `python main.py`
5. Acessar: http://localhost:5000
6. Login com admin/admin123 (ou valores do .env)

## 🚨 Importante

- **Nunca commite .env** no git (já está no .gitignore)
- **Mude ADMIN_PASS** em produção
- **Use SECRET_KEY aleatório** em produção
- **Adicione `?sslmode=require`** na DATABASE_URL se der erro de SSL

## 📊 Schema do Banco (já criado automaticamente)

```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT UNIQUE,
    password_hash TEXT,
    email TEXT UNIQUE,
    cnh TEXT,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Admin é inserido automaticamente na primeira execução.
