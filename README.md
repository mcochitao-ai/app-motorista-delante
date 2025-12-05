# App Motorista

Fluxo de encerramento de viagem com login/painel de usuários (Flask).

## Rodar local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY="devkey"
$env:ADMIN_USER="admin"
$env:ADMIN_PASS="admin123"
python main.py
```
Abra http://127.0.0.1:5000 (login em /login; painel admin em /dashboard).

## Estrutura
- main.py (Flask + SQLite)
- templates/ (Jinja: base, login, dashboard, trip_form)
- static/ (styles.css, app.js)
- requirements.txt
- render.yaml (deploy no Render via Gunicorn)

## Deploy no Render
- Conectar repo
- Build: `pip install -r requirements.txt`
- Start: `gunicorn main:app`
- Variáveis: SECRET_KEY, ADMIN_USER, ADMIN_PASS
- Opcional: disco persistente para app.db

## Próximos passos
- Persistir envios do formulário (salvar no banco ou API própria)
- Adicionar registro de localização/hora no envio
