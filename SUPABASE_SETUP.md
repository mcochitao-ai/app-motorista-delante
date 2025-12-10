# Configuração Supabase (PostgreSQL)

## Pré-requisitos
1. Conta no Supabase (https://supabase.com)
2. Projeto criado no Supabase

## Passos de Configuração

### 1. Obter String de Conexão do Supabase

No painel do Supabase:
1. Acesse seu projeto
2. Vá em **Settings** → **Database**
3. Em **Connection String**, escolha **URI** (não Pooler)
4. Copie a connection string no formato:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` (ou configure no servidor/Insights):

```bash
# Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Flask
SECRET_KEY=sua-chave-secreta-aqui-gere-com-openssl-rand-hex-32

# Admin padrão
ADMIN_USER=admin
ADMIN_PASS=senha-admin-segura

# Google OAuth (opcional)
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com

# Outras
FLASK_DEBUG=0
PORT=5000
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Inicializar Banco de Dados

O código cria automaticamente a tabela `users` no primeiro run:

```bash
python main.py
```

A tabela criada:
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

### 5. Verificar Conexão

Acesse: http://localhost:5000/health

Resposta esperada: `{"status": "ok"}`

## Deploy na Insights

### Variáveis de Ambiente Necessárias:
- `DATABASE_URL` (obrigatória)
- `SECRET_KEY` (obrigatória)
- `ADMIN_USER` (opcional, default: admin)
- `ADMIN_PASS` (opcional, default: admin123)
- `GOOGLE_CLIENT_ID` (se usar OAuth)

### Comando de Start:
```bash
gunicorn main:app --bind 0.0.0.0:$PORT
```

## Diferenças do SQLite → PostgreSQL

### ✅ Mudanças Implementadas:
1. **Imports**: `sqlite3` → `psycopg2`
2. **Connection Pool**: Gerenciamento de conexões com pool
3. **Placeholders**: `?` → `%s` em todas as queries
4. **Auto-increment**: `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
5. **Cursor Context**: Uso de `with db.cursor() as cur:`
6. **Exceptions**: `sqlite3.IntegrityError` → `psycopg2.IntegrityError`
7. **Rollback**: Adicionado `db.rollback()` em catches de erro

## Troubleshooting

### Erro: "DATABASE_URL environment variable is required"
Configure a variável `DATABASE_URL` no ambiente.

### Erro de conexão SSL
Adicione `?sslmode=require` no final da DATABASE_URL:
```
postgresql://...postgres?sslmode=require
```

### Verificar tabela criada no Supabase
No SQL Editor do Supabase:
```sql
SELECT * FROM users;
```

## Backup/Migração de Dados (se necessário)

Se tiver dados no SQLite local (`app.db`) e quiser migrar:

```bash
# Exportar do SQLite
sqlite3 app.db .dump > backup.sql

# Ajustar sintaxe manualmente e importar no Supabase SQL Editor
```
