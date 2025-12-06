# App Motorista - Delante

Um aplicativo web móvel para motoristas registrarem o término de suas entregas com suporte a Google OAuth e criação de perfil na primeira vez.

## 🎯 Recursos

### Autenticação
- **Login tradicional**: Usuário + Senha
- **Google OAuth**: Fazer login com Gmail
- **Registro de conta**: Criar nova conta com email
- **Perfil de motorista**: CNH, telefone e senha na primeira vez

### Painel de Motorista
- Dashboard com estatísticas (total de viagens, finalizadas, com devolução, hoje)
- Histórico de entregas recentes
- Formulário para encerrar viagem

### Formulário de Viagem
- **Data**: Auto-preenchida com data de hoje
- **Motorista**: Nome com opção de salvar no localStorage
- **Ajudante**: Nome (opcional)
- **Status**: Finalizado 100% ou Houve Devolução
- **Devoluções** (condicional): Quantidade, Número e motivo para cada uma
- **PIX** (condicional): Comprovante com upload
- **Canhoteira**: Múltiplas fotos com upload
- **Observações**: Campo de texto livre

### Admin
- Painel para criar usuários
- Tabela com usuários registrados

## 🚀 Como Iniciar

```bash
# Clone o repositório
git clone https://github.com/mcochitao-ai/app-motorista-delante.git
cd app-motorista-delante

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Execute
python main.py
```

Acesse http://localhost:5000

## 📋 Variáveis de Ambiente

- `SECRET_KEY`: Chave secreta Flask (padrão: "change-me")
- `ADMIN_USER`: Usuário admin (padrão: "admin")
- `ADMIN_PASS`: Senha admin (padrão: "admin123")
- `GOOGLE_CLIENT_ID`: Client ID do Google OAuth (veja GOOGLE_OAUTH_SETUP.md)

## 🔐 Fluxos de Autenticação

### Google OAuth + Primeira Vez
1. Clica "Sign in with Google"
2. Autentica com Gmail
3. Redireciona para completar perfil
4. Preenche CNH, telefone, senha
5. Acessa app

### Registro Tradicional
1. Clica "Criar Nova Conta"
2. Preenche Email, Nome, CNH, Telefone, Senha
3. Faz login
4. Acessa app

### Login Tradicional
1. Insere usuário/senha
2. Valida credenciais
3. Acessa app

## 📦 Stack

- Flask 3.0.3 + Python 3.13
- SQLite (dev) / PostgreSQL (prod)
- Autenticação: werkzeug + google-auth
- Frontend: HTML5, CSS3, Vanilla JS
- Hosting: Render.com (auto-deploy)
- WSGI: Gunicorn

## 📊 Banco de Dados

```
users:
  - id (PRIMARY KEY)
  - name, username, password_hash
  - email, cnh, phone
  - role (user/admin)
  - created_at
```

## 🚢 Deploy no Render

1. Conecte GitHub à Render
2. Crie Web Service
3. Configure variáveis:
   - `SECRET_KEY`: String aleatória
   - `ADMIN_USER`, `ADMIN_PASS`: Credenciais
   - `GOOGLE_CLIENT_ID`: Do Google Cloud

## 🎨 Cores

- Primary: `#00d4ff` (Cyan)
- Secondary: `#ff6b35` (Orange)
- Background: `#0a0e1a` (Dark Navy)

## 📱 Responsive

- Mobile-first
- Breakpoints: 640px, 800px
- Touch-friendly

## 🔒 Segurança

- ✅ Senhas hasheadas
- ✅ Sessions HTTP-only + SameSite
- ✅ OAuth tokens verificados
- ✅ Validação de usuário em cada request
- ✅ HTTPS recomendado

## 📁 Estrutura

```
app-motorista-delante/
├── main.py
├── requirements.txt
├── Procfile
├── render.yaml
├── GOOGLE_OAUTH_SETUP.md
├── README.md
├── static/
│   ├── styles.css
│   ├── app.js
│   └── Logo-Delante-Branco-scaled.webp
└── templates/
    ├── base.html
    ├── login.html
    ├── signup.html
    ├── profile_create.html
    ├── home.html
    ├── trip_form.html
    ├── dashboard.html
    ├── 403.html
    └── 404.html
```

## 💻 Endpoints

- `GET/POST /login` - Login
- `GET/POST /signup` - Registro
- `POST /auth/google/callback` - OAuth callback
- `GET/POST /profile/create` - Completar perfil
- `POST /logout` - Logout
- `GET /home` - Dashboard
- `GET/POST /form` - Formulário de viagem
- `GET/POST /dashboard` - Painel admin
- `GET /health` - Health check

---

**Desenvolvido para Delante** 🚚
