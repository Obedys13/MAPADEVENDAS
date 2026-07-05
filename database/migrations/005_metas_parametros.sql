-- Migration 005: Metas e Parâmetros do sistema
-- Grupo Doce Mel — Sistema Mapa de Vendas

CREATE TABLE IF NOT EXISTS metas_mensais (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ano               int  NOT NULL,
  mes               int  NOT NULL CHECK (mes BETWEEN 1 AND 12),
  vendedor          text NOT NULL,
  gestor            text,
  meta_valor        numeric(15,2) NOT NULL DEFAULT 0,
  meta_115_percent  numeric(15,2) GENERATED ALWAYS AS (meta_valor * 1.15) STORED,
  dias_uteis        int  NOT NULL DEFAULT 22,
  meta_diaria       numeric(15,2) GENERATED ALWAYS AS (
    CASE WHEN dias_uteis > 0 THEN meta_valor / dias_uteis ELSE 0 END
  ) STORED,
  CONSTRAINT uq_meta_ano_mes_vend UNIQUE (ano, mes, vendedor)
);

CREATE TABLE IF NOT EXISTS parametros_sistema (
  chave      varchar(100) PRIMARY KEY,
  valor      text         NOT NULL,
  descricao  text,
  updated_at timestamptz  NOT NULL DEFAULT now()
);

-- Parâmetros padrão iniciais
INSERT INTO parametros_sistema (chave, valor, descricao) VALUES
  ('margem_minima_percentual',    '15',   'Margem bruta mínima aceitável (%)'),
  ('desconto_maximo_percentual',  '10',   'Desconto máximo permitido sobre tabela (%)'),
  ('ruptura_critica_dias',        '3',    'Dias de estoque crítico para alerta de ruptura'),
  ('dias_uteis_mes_padrao',       '22',   'Quantidade padrão de dias úteis por mês'),
  ('meta_115_ativo',              'true', 'Calcular meta 115% ativa'),
  ('tema_padrao',                 'light','Tema padrão do sistema (light/dark)'),
  ('nome_empresa',                'Grupo Doce Mel', 'Nome da empresa'),
  ('divergencia_preco_alerta',    '5',    'Divergência de preço (%) que gera alerta')
ON CONFLICT (chave) DO NOTHING;

CREATE TABLE IF NOT EXISTS parametros_logistica (
  rota          varchar(50) PRIMARY KEY,
  nome_rota     text,
  valor_minimo  numeric(12,2) NOT NULL DEFAULT 0,
  tara_minima   numeric(10,3) NOT NULL DEFAULT 0,
  pedido_minimo numeric(12,2) NOT NULL DEFAULT 0,
  tipo_carro    varchar(50),
  frete_valor   numeric(10,2) NOT NULL DEFAULT 0,
  ativo         boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS usuarios (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome         text NOT NULL,
  email        text UNIQUE,
  password_hash text NOT NULL,
  perfil       varchar(20) NOT NULL DEFAULT 'visualizador',
  ativo        boolean NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now(),
  last_login   timestamptz
);
COMMENT ON COLUMN usuarios.perfil IS 'admin | gestor | vendedor | visualizador';

-- Usuário admin padrão (senha: mapaGDM@1 — substituir o hash em produção)
INSERT INTO usuarios (nome, email, password_hash, perfil)
VALUES ('Administrador', 'admin@docemei.com.br', '$2b$12$placeholder_hash_to_replace', 'admin')
ON CONFLICT (email) DO NOTHING;
