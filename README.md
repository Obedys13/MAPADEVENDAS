# Mapa de Vendas GDM — Beta 1.0

Sistema web de análise comercial do **Grupo Doce Mel**. Substitui o fluxo de planilhas Excel por um painel analítico interativo com uploads diários, KPIs em tempo real e gráficos de desempenho.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 18 + TypeScript + Tailwind CSS v3 + Vite 5 |
| Backend | Python 3.11 + FastAPI + pandas + openpyxl |
| Banco | Supabase (PostgreSQL) |
| Deploy | Vercel (frontend estático + backend serverless Python) |

---

## Funcionalidades (Beta 1.0)

- **Dashboard** — KPIs de Vendas, Margem, Meta, Realizado, Ruptura e Logística
- **Uploads diários** — Mapa de Vendas, Estoque, Lista de Preços, DDE, Meta por Vendedor
- **Filtros** — por período, vendedor, gestor, categoria, produto, rede, rota e outros
- **Gráficos** — Top categorias, por vendedor, evolução diária, rupturas
- **Tabela resumo** — por vendedor com venda bruta, líquida, margem
- **Temas** — claro e escuro
- **Mobile-first** — layout responsivo com BottomNav

---

## Estrutura do Projeto

```
APPMAPA/
├── frontend/          # React + Vite (deploy Vercel)
├── backend/           # FastAPI (deploy Railway)
├── database/          # Migrations SQL Supabase
├── .gitignore
├── README.md
└── DEPLOY.md
```

---

## Desenvolvimento Local

### Pré-requisitos

- Node.js 18+
- Python 3.11+
- Conta Supabase com as tabelas criadas (ver `database/migrations/`)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
cp .env.example .env            # preencha com suas credenciais
py -m uvicorn app.main:app --reload --port 8001
```

Backend disponível em: `http://localhost:8001`
Swagger UI: `http://localhost:8001/docs`

### Frontend

```bash
cd frontend
npm install
# Em desenvolvimento, o proxy /api já aponta para localhost:8001 (vite.config.ts)
npm run dev
```

Frontend disponível em: `http://localhost:5173`

---

## Variáveis de Ambiente

### Backend (`backend/.env`)

| Variável | Descrição |
|----------|-----------|
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon/public |
| `SUPABASE_SERVICE_KEY` | Chave service_role |
| `SECRET_KEY` | Chave JWT (min. 32 chars) |
| `ADMIN_PASSWORD` | Senha de acesso ao sistema |
| `APP_ENV` | `development` ou `production` |
| `CORS_ORIGINS` | Domínios permitidos (separados por vírgula) |

### Frontend (`frontend/.env`)

| Variável | Descrição |
|----------|-----------|
| `VITE_API_URL` | URL do backend Railway (produção) |

Em desenvolvimento o proxy Vite já encaminha `/api` para `http://localhost:8001`.

---

## Deploy

Consulte [DEPLOY.md](DEPLOY.md) para o guia passo a passo completo.

---

## Dados e Planilhas

O sistema processa os seguintes arquivos Excel:

| Planilha | Tipo | Frequência |
|----------|------|-----------|
| Mapa de Vendas | Diário | Substitui upload do mesmo dia |
| Estoque Analítico | Diário | Substitui upload do mesmo dia |
| Meta por Vendedor | Diário | Substitui upload do mesmo dia |
| DDE | Diário | Substitui upload do mesmo dia |
| Lista de Preços | Diário | Substitui upload do mesmo dia |
| Base de Produtos | Cadastral | Versionada |
| Planilha de Clientes | Cadastral | Versionada |

---

## Versão

**Beta 1.0** — Julho 2026
