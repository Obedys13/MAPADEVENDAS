-- Migration 004: Fatos e Resumos — tabelas desnormalizadas para KPIs
-- Grupo Doce Mel — Sistema Mapa de Vendas

CREATE TABLE IF NOT EXISTS fato_vendas (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data_referencia  date NOT NULL,
  upload_id        uuid REFERENCES uploads(id),
  -- Dimensões
  vendedor         text,
  gestor           text,
  cliente_codigo   text,
  produto_codigo   text,
  categoria        text,
  familia          text,
  grupo_produto    text,
  rede             text,
  rota             text,
  estado           text,
  tipo_saida       text,
  status_desconto  text,
  status_inteligente text,
  -- Medidas
  quantidade           numeric(12,3),
  venda_bruta          numeric(15,2),
  total_venda_liquida  numeric(15,2),
  total_margem_bruta   numeric(15,2),
  margem_percentual    numeric(8,4),
  desconto_tabela      numeric(8,4),
  divergencia_preco    numeric(15,2),
  ruptura_prevista     numeric(12,3),
  peso_total           numeric(12,3),
  ocupacao_peso        numeric(8,4),
  ocupacao_valor       numeric(8,4)
);

CREATE INDEX IF NOT EXISTS idx_fv_data     ON fato_vendas(data_referencia);
CREATE INDEX IF NOT EXISTS idx_fv_vendedor ON fato_vendas(vendedor);
CREATE INDEX IF NOT EXISTS idx_fv_gestor   ON fato_vendas(gestor);
CREATE INDEX IF NOT EXISTS idx_fv_categoria ON fato_vendas(categoria);
CREATE INDEX IF NOT EXISTS idx_fv_rede     ON fato_vendas(rede);
CREATE INDEX IF NOT EXISTS idx_fv_rota     ON fato_vendas(rota);
CREATE INDEX IF NOT EXISTS idx_fv_estado   ON fato_vendas(estado);
CREATE INDEX IF NOT EXISTS idx_fv_produto  ON fato_vendas(produto_codigo);
CREATE INDEX IF NOT EXISTS idx_fv_status_int ON fato_vendas(status_inteligente);

-- ─── Resumos pré-calculados ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS resumos_diarios (
  data_referencia          date PRIMARY KEY,
  total_venda_bruta        numeric(15,2),
  total_venda_liquida      numeric(15,2),
  total_margem_bruta       numeric(15,2),
  margem_media_percentual  numeric(8,4),
  qtd_pedidos              int,
  qtd_produtos             int,
  qtd_clientes             int,
  total_ruptura_kg         numeric(14,3),
  qtd_produtos_ruptura     int,
  qtd_categorias_ruptura   int,
  pedidos_viaveis          int,
  pedidos_aumentar_valor   int,
  pedidos_aumentar_peso    int,
  updated_at               timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resumos_vendedor (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data_referencia  date NOT NULL,
  vendedor         text NOT NULL,
  gestor           text,
  total_venda_bruta      numeric(15,2),
  total_venda_liquida    numeric(15,2),
  total_margem_bruta     numeric(15,2),
  margem_percentual      numeric(8,4),
  qtd_pedidos            int,
  meta_dia               numeric(15,2),
  atingimento_percentual numeric(8,4),
  status_meta            varchar(20),
  CONSTRAINT uq_resumo_vend_data UNIQUE (data_referencia, vendedor)
);

CREATE TABLE IF NOT EXISTS resumos_categoria (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data_referencia  date NOT NULL,
  categoria        text NOT NULL,
  total_venda_bruta    numeric(15,2),
  total_venda_liquida  numeric(15,2),
  total_margem_bruta   numeric(15,2),
  margem_percentual    numeric(8,4),
  quantidade           numeric(12,3),
  ruptura_kg           numeric(14,3),
  CONSTRAINT uq_resumo_cat_data UNIQUE (data_referencia, categoria)
);
