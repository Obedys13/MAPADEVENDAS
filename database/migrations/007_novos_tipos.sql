-- Migration 007: Novos tipos FIXAS + colunas para formatos novos
-- Grupo Doce Mel — Sistema Mapa de Vendas

-- ─── mapa_vendas_itens: colunas do novo formato ────────────────────────────
ALTER TABLE mapa_vendas_itens ADD COLUMN IF NOT EXISTS descr_grupo  varchar(100);
ALTER TABLE mapa_vendas_itens ADD COLUMN IF NOT EXISTS unidade      varchar(10);
ALTER TABLE mapa_vendas_itens ADD COLUMN IF NOT EXISTS data_emissao date;
ALTER TABLE mapa_vendas_itens ADD COLUMN IF NOT EXISTS data_saida   date;
ALTER TABLE mapa_vendas_itens ADD COLUMN IF NOT EXISTS data_entrega date;

-- ─── estoque_itens: colunas do novo formato ─────────────────────────────────
ALTER TABLE estoque_itens ADD COLUMN IF NOT EXISTS filial       varchar(20);
ALTER TABLE estoque_itens ADD COLUMN IF NOT EXISTS armz         varchar(20);
ALTER TABLE estoque_itens ADD COLUMN IF NOT EXISTS ult_preco    numeric(12,4);
ALTER TABLE estoque_itens ADD COLUMN IF NOT EXISTS nome_empresa varchar(100);
ALTER TABLE estoque_itens ADD COLUMN IF NOT EXISTS nome_filial  varchar(100);

-- ─── dim_vendedores: colunas para PLAN VENDEDORES ──────────────────────────
ALTER TABLE dim_vendedores ADD COLUMN IF NOT EXISTS upload_id    uuid REFERENCES uploads(id);
ALTER TABLE dim_vendedores ADD COLUMN IF NOT EXISTS nome_reduzido varchar(100);
ALTER TABLE dim_vendedores ADD COLUMN IF NOT EXISTS supervisor   varchar(200);
ALTER TABLE dim_vendedores ADD COLUMN IF NOT EXISTS gerente      varchar(200);

-- ─── base_categorias: mapeamento produto → categoria/família ───────────────
CREATE TABLE IF NOT EXISTS base_categorias (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id      uuid REFERENCES uploads(id),
  codigo         varchar(50),
  categoria      text,
  produto_codigo text,
  familia        text,
  grupo_produto  text,
  created_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_base_categ_produto ON base_categorias(produto_codigo);
CREATE INDEX IF NOT EXISTS idx_base_categ_categ   ON base_categorias(categoria);

-- ─── dim_tipos_tabela_preco: PLAN TIPOS TAB PREÇO ──────────────────────────
CREATE TABLE IF NOT EXISTS dim_tipos_tabela_preco (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id      uuid REFERENCES uploads(id),
  filial         varchar(100),
  cod_tabela     varchar(20),
  descricao      varchar(200),
  data_inicial   date,
  data_final     date,
  cond_pagto     varchar(50),
  tipo_horario   varchar(100),
  tab_ativa      varchar(20),
  ecommerce      varchar(20),
  created_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tipos_tab_preco_cod ON dim_tipos_tabela_preco(cod_tabela);

-- ─── dim_tabela_cliente_rota: TABELA X CLIENTE X ROTA ──────────────────────
CREATE TABLE IF NOT EXISTS dim_tabela_cliente_rota (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id     uuid REFERENCES uploads(id),
  nome          text,
  nome_fantasia text,
  estado        varchar(5),
  vendedor      varchar(20),
  grupo         varchar(20),
  tabela_preco  varchar(20),
  desconto      numeric(8,4),
  rota          varchar(100),
  rede          varchar(100),
  created_at    timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tab_cli_rota_rota     ON dim_tabela_cliente_rota(rota);
CREATE INDEX IF NOT EXISTS idx_tab_cli_rota_vendedor ON dim_tabela_cliente_rota(vendedor);

-- ─── dim_fretes: TABELA FRETES ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fretes (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id     uuid REFERENCES uploads(id),
  rota          text,
  carro         varchar(50),
  valor_atual   numeric(12,2),
  tara          numeric(12,2),
  pedido_minimo numeric(12,2),
  perc_despesa  numeric(10,6),
  created_at    timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_fretes_rota ON dim_fretes(rota);

-- ─── dim_grupo_rede: TABELA GRUPO REDE X CLIENTE ───────────────────────────
CREATE TABLE IF NOT EXISTS dim_grupo_rede (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id   uuid REFERENCES uploads(id),
  grupo       varchar(20),
  descricao   text,
  created_at  timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_grupo_rede_grupo ON dim_grupo_rede(grupo);

-- ─── dim_supervisor_vendedor: TABELA SUPERVISOR X VENDEDOR ─────────────────
CREATE TABLE IF NOT EXISTS dim_supervisor_vendedor (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id   uuid REFERENCES uploads(id),
  codigo      varchar(20),
  vendedor    text,
  local       varchar(100),
  supervisor  text,
  created_at  timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sup_vend_supervisor ON dim_supervisor_vendedor(supervisor);
