# Google OAuth Setup Guide

## Para implementar Google OAuth no Render, siga estes passos:

### 1. Criar projeto no Google Cloud Console

1. Vá para https://console.cloud.google.com/
2. Crie um novo projeto
3. Na barra de pesquisa, procure por "OAuth consent screen"
4. Configure como "External" app
5. Preencha as informações necessárias (app name, user support email, etc.)

### 2. Criar credenciais OAuth 2.0

1. Vá para "Credentials" no menu lateral
2. Clique em "Create Credentials" → "OAuth client ID"
3. Selecione "Web application"
4. Adicione as URIs autorizadas:
   - **Local**: `http://localhost:5000`
   - **Produção (Render)**: `https://seu-app.onrender.com`
5. Copie o "Client ID" - você precisará dele

### 3. Configurar no Render

1. Vá para seu app no Render Dashboard
2. Clique em "Environment"
3. Adicione uma nova variável:
   - **Key**: `GOOGLE_CLIENT_ID`
   - **Value**: Cole o Client ID que você copiou
4. Salve as alterações

### 4. Testar localmente

```bash
# Defina a variável de ambiente
export GOOGLE_CLIENT_ID="seu-client-id-aqui"

# Ou no Windows PowerShell:
$env:GOOGLE_CLIENT_ID="seu-client-id-aqui"

# Inicie o app
python main.py
```

### 5. Fluxo de uso

**Primeiro acesso (novo usuário):**
1. Clica em "Sign in with Google"
2. Autentica com Gmail
3. É redirecionado para "Completar Perfil"
4. Preencha CNH, telefone e define senha
5. Pronto! Pode acessar o app

**Acessos posteriores:**
1. Clica em "Sign in with Google"
2. Autentica com Gmail
3. Vai direto para Home

**Ou continua usando login tradicional:**
1. Usuário criado pelo signup form
2. Login com usuário/senha

## Notas de Segurança

- O token do Google é verificado no backend usando a biblioteca `google-auth`
- As senhas são sempre hasheadas com werkzeug.security
- Usuários OAuth ainda precisam definir uma senha (para login tradicional se necessário)
- CNH e telefone são campos obrigatórios no primeiro acesso

## Troubleshooting

### Erro "Token verification failed"
- Verifique se o GOOGLE_CLIENT_ID está correto no Render
- Certifique-se de que o domínio do Render está autorizado no Google Console

### Google Sign-In button não aparece
- Verifique se o GOOGLE_CLIENT_ID está sendo passado corretamente no template
- Verifique o console do navegador (F12) para erros JavaScript

### Usuário criado sem CNH/phone
- É normal! Na primeira vez, o usuário é criado e redirecionado para completar o perfil
- Isso evita solicitar muitos dados no OAuth callback do Google
