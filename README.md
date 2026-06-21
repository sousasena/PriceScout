# PriceScout 🔍

Plataforma de comparação de preços e avaliações de produtos, powered by Claude AI.

## Estrutura do projeto

```
pricescout/
├── app.py              ← Backend Flask (proxy seguro para a API)
├── requirements.txt    ← Dependências Python
├── Procfile            ← Para deploy no Render / Railway
├── .env.example        ← Modelo do arquivo de configuração
├── .gitignore
└── static/
    └── index.html      ← Frontend completo
```

---

## Rodando localmente

### 1. Clone / baixe o projeto

```bash
git clone https://github.com/SEU_USUARIO/pricescout.git
cd pricescout
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure a chave da API

```bash
cp .env.example .env
```

Abra o `.env` e substitua `sua_chave_aqui` pela sua chave real:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
FLASK_ENV=development
PORT=5000
```

> Sua chave está em: https://console.anthropic.com/settings/keys

### 4. Inicie o servidor

```bash
python app.py
```

Acesse: **http://localhost:5000**

---

## Deploy gratuito no Render

O Render oferece plano gratuito (pode dormir após 15 min de inatividade).

### Passo a passo:

1. **Suba o projeto no GitHub**
   ```bash
   git init
   git add .
   git commit -m "first commit"
   git remote add origin https://github.com/SEU_USUARIO/pricescout.git
   git push -u origin main
   ```

2. **Crie uma conta** em https://render.com

3. **Novo serviço** → *New Web Service* → conecte o repositório GitHub

4. **Configure o serviço:**
   | Campo            | Valor                        |
   |------------------|------------------------------|
   | Runtime          | Python 3                     |
   | Build Command    | `pip install -r requirements.txt` |
   | Start Command    | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

5. **Variáveis de ambiente** (aba *Environment*):
   ```
   ANTHROPIC_API_KEY = sk-ant-api03-...
   ```

6. Clique em **Deploy** — em alguns minutos sua URL estará disponível:
   `https://pricescout.onrender.com`

---

## Deploy no Railway

Alternativa ao Render, sem sleep automático no plano Trial.

1. Crie conta em https://railway.app
2. *New Project* → *Deploy from GitHub repo*
3. Adicione a variável `ANTHROPIC_API_KEY` em *Variables*
4. O Railway detecta o `Procfile` automaticamente e faz o deploy

---

## Variáveis de ambiente

| Variável           | Obrigatória | Descrição                              |
|--------------------|-------------|----------------------------------------|
| `ANTHROPIC_API_KEY`| ✅ Sim       | Chave da API Anthropic                 |
| `PORT`             | Não         | Porta do servidor (padrão: 5000)       |
| `FLASK_ENV`        | Não         | `development` ativa o modo debug       |

---

## Segurança

- A chave da API fica **somente no servidor** — nunca exposta no frontend
- O frontend chama `/api/search` no seu próprio domínio
- Validação de tamanho de query (máx 200 caracteres) para evitar abusos
- CORS configurado via `flask-cors`
