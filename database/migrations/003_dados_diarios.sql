-- Migration 003: Dados diários — Mapa de Vendas, Preços, Estoque, DDE
-- Grupo Doce Mel — Sistema Mapa de Vendas

-- ─── Mapa de Vendas ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mapa_vendas_uploads (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id      uuid REFERENCES uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL,
  CONSTRAINT uq_mapa_data UNIQUE (data_referencia)
);

CREATE TABLE IF NOT EXISTS mapa_vendas_itens (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mapa_upload_id   uuid REFERENCES mapa_vendas_uploads(id) ON DELETE CASCADE,
  data_referencia  date NOT NULL,
  -- Campos originais do Mapa
  grupo            varchar(50),
  codigo           varchar(20),
  descricao        text,
  fc               numeric(10,4),
  pedido           varchar(50),
  cliente_codigo   varchar(20),
  cliente_nome     text,
  data_pedido      date,
  quantidade       numeric(12,3),
  preco_cx         numeric(12,4),
  preco_tabela     numeric(12,4),
  custo_unitario   numeric(12,4),
  vendedor         varchar(100),
  gestor           varchar(100),
  estado           varchar(2),
  rede             varchar(100),
  rota             varchar(50),
  tipo_saida       varchar(50),
  peso_total       numeric(12,3),
  -- Campos calculados
  venda_bruta           numeric(15,2),
  venda_liquida_unit    numeric(15,4),
  total_venda_liquida   numeric(15,2),
  margem_unit           numeric(15,4),
  total_margem_bruta    numeric(15,2),
  margem_percentual     numeric(8,4),
  desconto_tabela       numeric(8,4),
  status_desconto       varchar(30),
  divergencia_preco     numeric(15,2),
  ruptura_prevista      numeric(12,3),
  -- Logística
  valor_rota            numeric(15,2),
  peso_rota             numeric(12,3),
  status_valor          varchar(20),
  status_peso           varchar(20),
  status_inteligente    varchar(20),
  ocupacao_peso         numeric(8,4),
  ocupacao_valor        numeric(8,4)
);

CREATE INDEX IF NOT EXISTS idx_mapa_itens_upload  ON mapa_vendas_itens(mapa_upload_id);
CREATE INDEX IF NOT EXISTS idx_mapa_itens_data    ON mapa_vendas_itens(data_referencia);
CREATE INDEX IF NOT EXISTS idx_mapa_itens_vend    ON mapa_vendas_itens(vendedor);
CREATE INDEX IF NOT EXISTS idx_mapa_itens_gestor  ON mapa_vendas_itens(gestor);
CREATE INDEX IF NOT EXISTS idx_mapa_itens_cat     ON mapa_vendas_itens(grupo);
CREATE INDEX IF NOT EXISTS idx_mapa_itens_rede    ON mapa_vendas_itens(rede);
CREATE INDEX IF NOT EXISTS idx_mapa_itens_rota    ON mapa_vendas_itens(rota);

-- ─── Lista de Preços ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lista_precos_uploads (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id      uuid REFERENCES uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL,
  cod_tabela     varchar(20)
);

CREATE TABLE IF NOT EXISTS lista_precos_itens (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lp_upload_id    uuid REFERENCES lista_precos_uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL,
  cod_tabela      varchar(20),
  descricao_tabela text,
  codigo          varchar(20),
  descricao       text,
  unidade         varchar(10),
  preco_base      numeric(12,4),
  preco_venda     numeric(12,4),
  vlr_desconto    numeric(12,4),
  data_inicial    date,
  data_final      date,
  estado          varchar(2),
  tipo_operacao   varchar(20)
);

CREATE INDEX IF NOT EXISTS idx_lp_itens_upload ON lista_precos_itens(lp_upload_id);
CREATE INDEX IF NOT EXISTS idx_lp_itens_codigo ON lista_precos_itens(codigo);
CREATE INDEX IF NOT EXISTS idx_lp_itens_tabela ON lista_precos_itens(cod_tabela);

-- ─── Estoque Analítico ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estoque_uploads (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id      uuid REFERENCES uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL
);

CREATE TABLE IF NOT EXISTS estoque_itens (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  est_upload_id   uuid REFERENCES estoque_uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL,
  codigo          varchar(20),
  descricao       text,
  unidade         varchar(10),
  estoque_kg      numeric(14,3),
  estoque_pc      numeric(14,3),
  custo_unitario  numeric(12,4),
  valor_estoque   numeric(15,2),
  dias_estoque    numeric(8,2)
);

CREATE INDEX IF NOT EXISTS idx_est_itens_upload ON estoque_itens(est_upload_id);
CREATE INDEX IF NOT EXISTS idx_est_itens_codigo ON estoque_itens(codigo);

-- ─── DDE ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dde_uploads (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id      uuid REFERENCES uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL
);

CREATE TABLE IF NOT EXISTS dde_itens (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dde_upload_id   uuid REFERENCES dde_uploads(id) ON DELETE CASCADE,
  data_referencia date NOT NULL,
  categoria       text NOT NULL,
  meta_kg         numeric(14,3),
  venda_kg        numeric(14,3),
  estoque_kg      numeric(14,3),
  custo_unitario  numeric(12,4),
  estoque_pc      numeric(14,3),
  perc_av         numeric(8,4),
  ressuprimento   numeric(14,3),
  dias_esperado   numeric(8,2),
  dias_estoque    numeric(8,2),
  excesso_rs      numeric(15,2),
  excesso_kg      numeric(14,3),
  ruptura_kg      numeric(14,3),
  perc_resultado  numeric(8,4)
);

CREATE INDEX IF NOT EXISTS idx_dde_itens_upload    ON dde_itens(dde_upload_id);
CREATE INDEX IF NOT EXISTS idx_dde_itens_data      ON dde_itens(data_referencia);
CREATE INDEX IF NOT EXISTS idx_dde_itens_categoria ON dde_itens(categoria);
