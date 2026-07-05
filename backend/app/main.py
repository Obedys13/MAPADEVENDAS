from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes import auth, uploads, dashboard, analises, relatorios, configuracoes

app = FastAPI(
    title="Grupo Doce Mel — Sistema Mapa de Vendas",
    description="API REST para análise diária do Mapa de Vendas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(analises.router)
app.include_router(relatorios.router)
app.include_router(configuracoes.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "sistema": "Grupo Doce Mel — Mapa de Vendas", "versao": "1.0.0"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
