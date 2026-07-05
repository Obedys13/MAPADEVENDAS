# Guia de Deploy — Mapa de Vendas GDM (Beta 1.0)

Arquitetura:
- **Frontend** → [Vercel](https://vercel.com) (React + Vite, SPA estático)
- **Backend** → [Railway](https://railway.app) (FastAPI + pandas, servidor persistente)
- **Banco** → [Supabase](https://supabase.com) (PostgreSQL, já configurado)

---

## Parte 1 — Preparar o Repositório Git

### 1.1 Inicializar e enviar para o GitHub

```bash
# Na raiz do projeto APPMAPA:
git init
git add .
git commit -m "Beta 1.0 — sistema web Mapa de Vendas GDM"
git branch -M main
git remote add origin https://github.com/Obedys13/MAPADEVENDAS.git
git push -u origin main
```

> **Atenção**: o `.gitignore` já exclui `*.xlsx`, `*.env`, `node_modules/` e `dist/`.
> Nunca commite arquivos `.env` com credenciais reais.

---

## Parte 2 — Deploy do Backend no Railway

### 2.1 Criar conta e novo projeto

1. Acesse [railway.app](https://railway.app) e faça login com GitHub
2. Clique em **New Project** → **Deploy from GitHub repo**
3. Selecione o repositório `Obedys13/MAPADEVENDAS`

### 2.2 Configurar o serviço

1. Após criar o projeto, clique no serviço criado
2. Vá em **Settings → Source**:
   - **Root Directory**: `backend`
3. Vá em **Settings → Deploy**:
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - (ou deixe o `railway.toml` cuidar disso automaticamente)

### 2.3 Adicionar variáveis de ambiente

No Railway, vá em **Variables** e adicione:

```
SUPABASE_URL        = https://xxxxxxxxxxxxxxxxxxxx.supabase.co
SUPABASE_KEY        = <sua anon key>
SUPABASE_SERVICE_KEY= <sua service_role key>
SECRET_KEY          = <chave aleatória, ex: openssl rand -hex 32>
ADMIN_PASSWORD      = <sua senha de acesso>
APP_ENV             = production
CORS_ORIGINS        = https://seu-app.vercel.app
```

> O `CORS_ORIGINS` será atualizado após o deploy do frontend (Step 3.3).

### 2.4 Fazer o deploy

1. O Railway faz deploy automático ao detectar o `Procfile` e `requirements.txt`
2. Aguarde o build (~2-3 minutos)
3. Clique em **Generate Domain** para obter a URL pública
   - Exemplo: `https://mapadevendas-production.up.railway.app`
4. Teste: `https://mapadevendas-production.up.railway.app/health`
   - Deve retornar `{"status": "ok"}`

---

## Parte 3 — Deploy do Frontend na Vercel

### 3.1 Criar conta e importar projeto

1. Acesse [vercel.com](https://vercel.com) e faça login com GitHub
2. Clique em **Add New → Project**
3. Importe o repositório `Obedys13/MAPADEVENDAS`

### 3.2 Configurar o projeto

Na tela de configuração:

| Campo | Valor |
|-------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

### 3.3 Adicionar variável de ambiente

Em **Environment Variables**, adicione:

```
VITE_API_URL = https://mapadevendas-production.up.railway.app
```

> Use a URL do Railway que você obteve no Step 2.3.

### 3.4 Fazer o deploy

1. Clique em **Deploy**
2. Aguarde (~1-2 minutos)
3. A Vercel fornecerá uma URL pública:
   - Exemplo: `https://mapadevendas-abc123.vercel.app`

### 3.5 Atualizar CORS no Railway

Volte ao Railway → Variables e atualize:

```
CORS_ORIGINS = https://mapadevendas-abc123.vercel.app
```

Adicione o domínio personalizado se tiver (ex: `https://mapa.grupodomecmel.com.br`).

Depois disso, vá em **Deployments → Redeploy** para aplicar a mudança.

---

## Parte 4 — Verificação Final

### Checklist pós-deploy

- [ ] `https://SEU-BACKEND.up.railway.app/health` retorna `{"status": "ok"}`
- [ ] `https://SEU-FRONTEND.vercel.app` abre a tela de login
- [ ] Login com a senha configurada em `ADMIN_PASSWORD` funciona
- [ ] Página Upload consegue enviar um arquivo (teste com Mapa de Vendas)
- [ ] Dashboard carrega os KPIs após o upload
- [ ] Tema escuro/claro funcionando
- [ ] Layout responsivo no celular

---

## Parte 5 — Domínio Personalizado (opcional)

### Vercel (frontend)
1. Vá em **Settings → Domains**
2. Adicione seu domínio (ex: `mapa.grupodomecmel.com.br`)
3. Configure o DNS conforme instruído pela Vercel (registro CNAME ou A)

### Railway (backend)
1. Vá em **Settings → Networking → Custom Domain**
2. Adicione o subdomínio da API (ex: `api.grupodomecmel.com.br`)
3. Atualize `CORS_ORIGINS` no Railway com o novo domínio do frontend

---

## Parte 6 — Atualizações Futuras

Para enviar novas versões:

```bash
# Commitar e enviar as alterações
git add .
git commit -m "descrição da mudança"
git push origin main
```

- **Vercel** faz redeploy automático ao receber o push na branch `main`
- **Railway** faz redeploy automático ao receber o push na branch `main`

---

## Referência Rápida

| Serviço | URL |
|---------|-----|
| Repositório | https://github.com/Obedys13/MAPADEVENDAS |
| Vercel Dashboard | https://vercel.com/dashboard |
| Railway Dashboard | https://railway.app/dashboard |
| Supabase Dashboard | https://supabase.com/dashboard |
| Swagger Backend | https://SEU-BACKEND.up.railway.app/docs |
