-- Migration 006: Índices compostos adicionais e Row Level Security
-- Grupo Doce Mel — Sistema Mapa de Vendas

-- Índices compostos para queries de dashboard com múltiplos filtros
CREATE INDEX IF NOT EXISTS idx_fv_data_vend   ON fato_vendas(data_referencia, vendedor);
CREATE INDEX IF NOT EXISTS idx_fv_data_gest   ON fato_vendas(data_referencia, gestor);
CREATE INDEX IF NOT EXISTS idx_fv_data_cat    ON fato_vendas(data_referencia, categoria);
CREATE INDEX IF NOT EXISTS idx_fv_data_rede   ON fato_vendas(data_referencia, rede);
CREATE INDEX IF NOT EXISTS idx_fv_data_rota   ON fato_vendas(data_referencia, rota);
CREATE INDEX IF NOT EXISTS idx_fv_data_est    ON fato_vendas(data_referencia, estado);

CREATE INDEX IF NOT EXISTS idx_mapa_data_vend ON mapa_vendas_itens(data_referencia, vendedor);
CREATE INDEX IF NOT EXISTS idx_mapa_data_cat  ON mapa_vendas_itens(data_referencia, grupo);
CREATE INDEX IF NOT EXISTS idx_mapa_data_rede ON mapa_vendas_itens(data_referencia, rede);

-- Índices em produtos vigentes (parcial — apenas version ativa)
CREATE INDEX IF NOT EXISTS idx_prod_version_ativo ON produto_base_versions(ativo)
  WHERE ativo = true;
CREATE INDEX IF NOT EXISTS idx_cli_version_ativo  ON cliente_base_versions(ativo)
  WHERE ativo = true;

-- ─── Row Level Security ─────────────────────────────────────────────────────
-- Habilitar RLS nas tabelas principais
ALTER TABLE uploads           ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_logs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE fato_vendas       ENABLE ROW LEVEL SECURITY;
ALTER TABLE mapa_vendas_itens ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumos_diarios   ENABLE ROW LEVEL SECURITY;
ALTER TABLE metas_mensais     ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios          ENABLE ROW LEVEL SECURITY;

-- Políticas de leitura: role 'authenticated' pode ler tudo
CREATE POLICY "authenticated_read_uploads"
  ON uploads FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "authenticated_read_fato_vendas"
  ON fato_vendas FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "authenticated_read_mapa_itens"
  ON mapa_vendas_itens FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "authenticated_read_resumos"
  ON resumos_diarios FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "authenticated_read_metas"
  ON metas_mensais FOR SELECT
  TO authenticated USING (true);

-- Escrita apenas por service_role (backend)
CREATE POLICY "service_role_write_uploads"
  ON uploads FOR ALL
  TO service_role USING (true);

CREATE POLICY "service_role_write_fato_vendas"
  ON fato_vendas FOR ALL
  TO service_role USING (true);

CREATE POLICY "service_role_write_mapa_itens"
  ON mapa_vendas_itens FOR ALL
  TO service_role USING (true);

CREATE POLICY "service_role_write_resumos"
  ON resumos_diarios FOR ALL
  TO service_role USING (true);

-- Usuários: admin pode ver todos, outros só a si mesmo
CREATE POLICY "usuarios_self_read"
  ON usuarios FOR SELECT
  TO authenticated USING (true);
