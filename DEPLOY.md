# Guia de Deploy — Mapa de Vendas GDM (Beta 1.0)

Arquitetura **full-stack na Vercel**:
- **Frontend** (React + Vite) → servido como arquivos estáticos
- **Backend** (FastAPI + pandas) → função serverless Python em `/api`
- **Banco** → Supabase (PostgreSQL, já configurado)

---

## Parte 1 — Enviar o Código para o GitHub

```bash
# Na raiz do projeto APPMAPA (já feito se você está aqui pela primeira vez):
git add .
git commit -m "configuração Vercel full-stack"
git push origin main
```

> **Atenção**: o `.gitignore` já exclui `*.xlsx`, `*.env`, `node_modules/` e `dist/`.
> Nunca commite arquivos `.env` com credenciais reais.

---

## Parte 2 — Deploy na Vercel

### 2.1 Criar conta e importar projeto

1. Acesse [vercel.com](https://vercel.com) e faça login com GitHub
2. Clique em **Add New → Project**
3. Selecione o repositório **`Obedys13/MAPADEVENDAS`**

### 2.2 Configurar o projeto

Na tela de configuração, **não altere** o Framework Preset — o `vercel.json` na raiz já configura tudo:

| Campo | Valor (preenchido automático) |
|-------|-------------------------------|
| Root Directory | `. (raiz)` |
| Build Command | `cd frontend && npm install && npm run build` |
| Output Directory | `frontend/dist` |

### 2.3 Adicionar variáveis de ambiente

Clique em **Environment Variables** e adicione:

| Nome | Valor |
|------|-------|
| `SUPABASE_URL` | `https://xxxxxxxxxxxxxxxxxxxx.supabase.co` |
| `SUPABASE_KEY` | sua anon/public key |
| `SUPABASE_SERVICE_KEY` | sua service_role key |
| `SECRET_KEY` | chave aleatória (ex: rode `openssl rand -hex 32`) |
| `ADMIN_PASSWORD` | sua senha de acesso ao sistema |
| `APP_ENV` | `production` |
| `CORS_ORIGINS` | `*` (ou o domínio exato após o primeiro deploy) |

> **Importante**: `VITE_API_URL` **não é necessária** — frontend e backend ficam
> no mesmo domínio Vercel, então as chamadas `/api/...` são same-origin.

### 2.4 Fazer o deploy

1. Clique em **Deploy**
2. Aguarde (~2-3 minutos para build do frontend + bundle Python)
3. A Vercel fornecerá a URL pública:
   - Exemplo: `https://mapadevendas.vercel.app`

---

## Parte 3 — Verificação

### Checklist pós-deploy

- [ ] `https://SEU-APP.vercel.app/api/health` retorna `{"status":"healthy"}`
- [ ] `https://SEU-APP.vercel.app` abre a tela de login
- [ ] Login com a senha definida em `ADMIN_PASSWORD` funciona
- [ ] Upload de planilha funciona (teste com Mapa de Vendas)
- [ ] Dashboard carrega os KPIs após upload
- [ ] Tema escuro/claro funcionando
- [ ] Layout responsivo no celular

---

## Parte 4 — Domínio Personalizado (opcional)

1. Vá em **Settings → Domains**
2. Adicione seu domínio (ex: `mapa.grupodomecmel.com.br`)
3. Configure o DNS conforme instruído (registro CNAME ou A)
4. Atualize `CORS_ORIGINS` para o domínio personalizado e clique em **Redeploy**

---

## Parte 5 — Atualizações Futuras

```bash
git add .
git commit -m "descrição da mudança"
git push origin main
```

A Vercel faz redeploy automático ao receber o push na branch `main`.

---

## Limites Importantes (Plano Hobby Vercel)

| Recurso | Limite |
|---------|--------|
| Duração da função Python | 60 segundos |
| Memória da função | 1024 MB |
| Tamanho do bundle (função) | 250 MB |
| Tamanho do corpo da requisição | 4.5 MB |

> O limite de 4.5 MB para uploads pode ser um problema para planilhas Excel muito grandes.
> Se os arquivos Excel ultrapassarem esse tamanho, considere compactar antes do upload.

---

## Como Funciona Internamente

```
Browser → GET /                → Vercel serve frontend/dist/index.html
Browser → POST /api/auth/login → Vercel roteia para api/index.py (FastAPI)
Browser → POST /api/uploads/.. → Vercel roteia para api/index.py (FastAPI)
```

`api/index.py` remove o prefixo `/api` e passa a requisição ao FastAPI,
que processa com pandas/openpyxl e persiste no Supabase.

---

## Referência Rápida

| Serviço | URL |
|---------|-----|
| Repositório | https://github.com/Obedys13/MAPADEVENDAS |
| Vercel Dashboard | https://vercel.com/dashboard |
| Supabase Dashboard | https://supabase.com/dashboard |
| Swagger (produção) | https://SEU-APP.vercel.app/api/docs |
| Swagger (local) | http://localhost:8001/docs |
