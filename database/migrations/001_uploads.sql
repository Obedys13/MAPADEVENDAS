-- Migration 001: Controle de Uploads
-- Grupo Doce Mel — Sistema Mapa de Vendas

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS uploads (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tipo          varchar(50)  NOT NULL,
  data_referencia date,
  arquivo_original text,
  usuario       text         NOT NULL DEFAULT 'admin',
  data_hora_upload timestamptz NOT NULL DEFAULT now(),
  status        varchar(20)  NOT NULL DEFAULT 'pendente',
  total_registros      int,
  registros_processados int,
  mensagem_erro text,
  substituido_por uuid REFERENCES uploads(id)
);

COMMENT ON COLUMN uploads.tipo IS
  'mapa_vendas | lista_precos | estoque | dde | base_produtos | planilha_produtos | base_clientes | planilha_clientes';
COMMENT ON COLUMN uploads.status IS
  'pendente | processando | concluido | erro';

CREATE TABLE IF NOT EXISTS upload_logs (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id  uuid REFERENCES uploads(id) ON DELETE CASCADE,
  nivel      varchar(10) NOT NULL DEFAULT 'info',
  mensagem   text        NOT NULL,
  linha      int,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uploads_tipo_data ON uploads(tipo, data_referencia);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_upload_logs_upload ON upload_logs(upload_id);
