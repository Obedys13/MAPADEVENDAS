-- Migration 002: Dimensões — Bases cadastrais versionadas
-- Grupo Doce Mel — Sistema Mapa de Vendas

-- ─── Versões de Produtos ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS produto_base_versions (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id              uuid REFERENCES uploads(id),
  tipo_base              varchar(30) NOT NULL DEFAULT 'base_produtos',
  data_upload            date  NOT NULL,
  periodo_inicio_vigencia date  NOT NULL,
  periodo_fim_vigencia   date,
  ativo                  boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS produtos (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_id   uuid REFERENCES produto_base_versions(id) ON DELETE CASCADE,
  codigo       varchar(20) NOT NULL,
  descricao    text,
  unidade      varchar(10),
  categoria    varchar(100),
  familia      varchar(100),
  grupo_produto varchar(100),
  -- Campos adicionais de PLANILHA PRODUTOS GERAL
  tipo         varchar(20),
  fator_conversao numeric(10,4),
  peso_liquido    numeric(10,3),
  peso_bruto      numeric(10,3),
  cod_categoria   varchar(20),
  cod_familia     varchar(20),
  fabricante      varchar(100),
  marca           varchar(100),
  qtd_cx_palet    int
);

CREATE INDEX IF NOT EXISTS idx_produtos_version ON produtos(version_id);
CREATE INDEX IF NOT EXISTS idx_produtos_codigo  ON produtos(codigo);

-- ─── Versões de Clientes ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cliente_base_versions (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id              uuid REFERENCES uploads(id),
  tipo_base              varchar(30) NOT NULL DEFAULT 'base_clientes',
  data_upload            date  NOT NULL,
  periodo_inicio_vigencia date  NOT NULL,
  periodo_fim_vigencia   date,
  ativo                  boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS clientes (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_id   uuid REFERENCES cliente_base_versions(id) ON DELETE CASCADE,
  codigo       varchar(20) NOT NULL,
  loja         varchar(10),
  nome         text,
  nome_fantasia text,
  estado       varchar(2),
  municipio    varchar(100),
  cep          varchar(10),
  vendedor     varchar(100),
  grupo_vendas varchar(100),
  regiao       varchar(100),
  tabela_preco varchar(20),
  desconto     numeric(5,2),
  rota         varchar(50),
  rede         varchar(100),
  tipo         varchar(50),
  bloqueado    boolean DEFAULT false,
  ativo        boolean DEFAULT true,
  latitude     numeric(10,6),
  longitude    numeric(10,6)
);

CREATE INDEX IF NOT EXISTS idx_clientes_version  ON clientes(version_id);
CREATE INDEX IF NOT EXISTS idx_clientes_codigo   ON clientes(codigo);
CREATE INDEX IF NOT EXISTS idx_clientes_vendedor ON clientes(vendedor);
CREATE INDEX IF NOT EXISTS idx_clientes_rede     ON clientes(rede);
CREATE INDEX IF NOT EXISTS idx_clientes_rota     ON clientes(rota);

-- ─── Dimensões fixas ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_vendedores (
  id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo  varchar(20),
  nome    text NOT NULL,
  gestor  text,
  ativo   boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_gestores (
  id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome  text NOT NULL UNIQUE,
  ativo boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_redes (
  id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo varchar(20),
  nome   text NOT NULL,
  ativo  boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_rotas (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo         varchar(20) NOT NULL UNIQUE,
  nome           text,
  valor_minimo   numeric(12,2),
  tara_minima    numeric(10,3),
  pedido_minimo  numeric(12,2),
  tipo_carro     varchar(50),
  frete          numeric(10,2),
  ativo          boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS dim_categorias (
  id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo  varchar(20),
  nome    text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_familias (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo       varchar(20),
  nome         text NOT NULL,
  categoria_id uuid REFERENCES dim_categorias(id)
);
