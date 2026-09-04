-- =============================================================================
-- Sistema Meu Bazar — Schema do Banco de Dados
-- 13 tabelas | MySQL 8 | InnoDB | utf8mb4
-- Regime: ME — Lucro Presumido (CST)
-- =============================================================================

-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS sistema_meu_bazar
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sistema_meu_bazar;

-- =============================================================================
-- 1. USUARIOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100)    NOT NULL,
    login           VARCHAR(50)     NOT NULL UNIQUE,
    senha_hash      VARCHAR(255)    NOT NULL,
    perfil          ENUM('operador', 'gerente', 'admin') NOT NULL DEFAULT 'operador',
    ativo           BOOLEAN         NOT NULL DEFAULT TRUE,
    criado_em       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_usuarios_login (login),
    INDEX idx_usuarios_perfil (perfil),
    INDEX idx_usuarios_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 2. CATEGORIAS
-- =============================================================================
CREATE TABLE IF NOT EXISTS categorias (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100)    NOT NULL UNIQUE,
    descricao       VARCHAR(255)    DEFAULT NULL,
    ativa           BOOLEAN         NOT NULL DEFAULT TRUE,
    criado_em       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_categorias_ativa (ativa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 3. PRODUTOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS produtos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codigo_barras   VARCHAR(20)     DEFAULT NULL UNIQUE,
    codigo_interno  VARCHAR(20)     NOT NULL UNIQUE,
    nome            VARCHAR(200)    NOT NULL,
    descricao       TEXT            DEFAULT NULL,
    categoria_id    INT             DEFAULT NULL,
    preco_custo     DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    preco_venda     DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    margem_lucro    DECIMAL(8,2)    NOT NULL DEFAULT 0.00,

    -- Campos fiscais (Lucro Presumido — CST)
    ncm             VARCHAR(10)     DEFAULT NULL,
    cst_icms        VARCHAR(3)      DEFAULT '00',
    cst_pis         VARCHAR(2)      DEFAULT '01',
    cst_cofins      VARCHAR(2)      DEFAULT '01',
    aliquota_icms   DECIMAL(5,2)    DEFAULT 0.00,
    cfop            VARCHAR(4)      DEFAULT '5102',
    unidade         VARCHAR(5)      NOT NULL DEFAULT 'UN',

    -- Estoque
    estoque_atual   DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    estoque_minimo  DECIMAL(12,3)   NOT NULL DEFAULT 0.000,

    ativo           BOOLEAN         NOT NULL DEFAULT TRUE,
    criado_em       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_produtos_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_produtos_codigo_barras (codigo_barras),
    INDEX idx_produtos_codigo_interno (codigo_interno),
    INDEX idx_produtos_nome (nome),
    INDEX idx_produtos_categoria (categoria_id),
    INDEX idx_produtos_ativo (ativo),
    INDEX idx_produtos_estoque (estoque_atual, estoque_minimo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 4. CLIENTES
-- =============================================================================
CREATE TABLE IF NOT EXISTS clientes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(150)    NOT NULL,
    cpf_cnpj        VARCHAR(18)     DEFAULT NULL UNIQUE,
    telefone        VARCHAR(20)     DEFAULT NULL,
    email           VARCHAR(150)    DEFAULT NULL,
    endereco        VARCHAR(255)    DEFAULT NULL,
    cidade          VARCHAR(100)    DEFAULT NULL,
    uf              CHAR(2)         DEFAULT NULL,
    cep             VARCHAR(10)     DEFAULT NULL,
    observacao      TEXT            DEFAULT NULL,
    ativo           BOOLEAN         NOT NULL DEFAULT TRUE,
    criado_em       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_clientes_nome (nome),
    INDEX idx_clientes_cpf_cnpj (cpf_cnpj),
    INDEX idx_clientes_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 5. TURNOS
-- =============================================================================
CREATE TABLE IF NOT EXISTS turnos (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id          INT             NOT NULL,
    valor_abertura      DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    valor_fechamento    DECIMAL(12,2)   DEFAULT NULL,
    total_vendas        DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    total_cancelamentos DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    total_sangrias      DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    total_suprimentos   DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    diferenca           DECIMAL(12,2)   DEFAULT NULL,
    qtd_vendas          INT             NOT NULL DEFAULT 0,
    abertura            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fechamento          DATETIME        DEFAULT NULL,
    status              ENUM('aberto', 'fechado') NOT NULL DEFAULT 'aberto',
    observacao          TEXT            DEFAULT NULL,

    CONSTRAINT fk_turnos_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_turnos_usuario (usuario_id),
    INDEX idx_turnos_status (status),
    INDEX idx_turnos_abertura (abertura)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 6. VENDAS
-- =============================================================================
CREATE TABLE IF NOT EXISTS vendas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    turno_id        INT             NOT NULL,
    cliente_id      INT             DEFAULT NULL,
    usuario_id      INT             NOT NULL,
    subtotal        DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    desconto        DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    total           DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    valor_recebido  DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    troco           DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    status          ENUM('finalizada', 'cancelada', 'contingencia')
                                    NOT NULL DEFAULT 'finalizada',

    -- Dados fiscais (NFC-e)
    nfce_numero     VARCHAR(20)     DEFAULT NULL,
    nfce_chave      VARCHAR(50)     DEFAULT NULL,
    nfce_protocolo  VARCHAR(20)     DEFAULT NULL,
    nfce_pdf_url    TEXT            DEFAULT NULL,
    nfce_status     VARCHAR(20)     DEFAULT NULL,

    criado_em       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_vendas_turno
        FOREIGN KEY (turno_id) REFERENCES turnos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_vendas_cliente
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_vendas_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_vendas_turno (turno_id),
    INDEX idx_vendas_cliente (cliente_id),
    INDEX idx_vendas_usuario (usuario_id),
    INDEX idx_vendas_status (status),
    INDEX idx_vendas_criado_em (criado_em),
    INDEX idx_vendas_nfce_chave (nfce_chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 7. VENDA_ITENS
-- =============================================================================
CREATE TABLE IF NOT EXISTS venda_itens (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    venda_id        INT             NOT NULL,
    produto_id      INT             NOT NULL,
    quantidade      DECIMAL(12,3)   NOT NULL DEFAULT 1.000,
    preco_unitario  DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    desconto_item   DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    subtotal        DECIMAL(12,2)   NOT NULL DEFAULT 0.00,

    CONSTRAINT fk_venda_itens_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_venda_itens_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_venda_itens_venda (venda_id),
    INDEX idx_venda_itens_produto (produto_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 8. PAGAMENTOS_VENDA
-- =============================================================================
CREATE TABLE IF NOT EXISTS pagamentos_venda (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    venda_id        INT             NOT NULL,
    forma           ENUM('dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'cheque', 'outros')
                                    NOT NULL,
    valor           DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    bandeira        VARCHAR(30)     DEFAULT NULL,
    nsu             VARCHAR(30)     DEFAULT NULL,
    autorizacao     VARCHAR(30)     DEFAULT NULL,
    parcelas        INT             NOT NULL DEFAULT 1,

    CONSTRAINT fk_pagamentos_venda
        FOREIGN KEY (venda_id) REFERENCES vendas(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    INDEX idx_pagamentos_venda (venda_id),
    INDEX idx_pagamentos_forma (forma)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 9. NOTAS_ENTRADA (NF-e de compra importadas)
-- Precisa ser criada ANTES de movimentacoes_estoque (que a referencia via FK)
-- =============================================================================
CREATE TABLE IF NOT EXISTS notas_entrada (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    chave_nfe           VARCHAR(44)     NOT NULL UNIQUE,
    numero_nfe          VARCHAR(20)     DEFAULT NULL,
    serie               VARCHAR(5)      DEFAULT NULL,
    fornecedor_cnpj     VARCHAR(18)     DEFAULT NULL,
    fornecedor_nome     VARCHAR(200)    DEFAULT NULL,
    data_emissao        DATETIME        DEFAULT NULL,
    valor_total         DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    xml_path            VARCHAR(500)    DEFAULT NULL,
    usuario_id          INT             NOT NULL,
    importado_em        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacao          TEXT            DEFAULT NULL,

    CONSTRAINT fk_notas_entrada_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_notas_entrada_chave (chave_nfe),
    INDEX idx_notas_entrada_fornecedor (fornecedor_cnpj),
    INDEX idx_notas_entrada_data (data_emissao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 10. NOTAS_ENTRADA_ITENS
-- =============================================================================
CREATE TABLE IF NOT EXISTS notas_entrada_itens (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    nota_entrada_id     INT             NOT NULL,
    produto_id          INT             DEFAULT NULL,
    numero_item         INT             NOT NULL DEFAULT 1,
    codigo_ean          VARCHAR(20)     DEFAULT NULL,
    nome_produto_nfe    VARCHAR(200)    NOT NULL,
    ncm                 VARCHAR(10)     DEFAULT NULL,
    cfop                VARCHAR(4)      DEFAULT NULL,
    unidade             VARCHAR(5)      DEFAULT NULL,
    quantidade          DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    valor_unitario      DECIMAL(12,4)   NOT NULL DEFAULT 0.0000,
    valor_total         DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    vinculado           BOOLEAN         NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_nota_itens_nota
        FOREIGN KEY (nota_entrada_id) REFERENCES notas_entrada(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_nota_itens_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_nota_itens_nota (nota_entrada_id),
    INDEX idx_nota_itens_produto (produto_id),
    INDEX idx_nota_itens_ean (codigo_ean)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 11. MOVIMENTACOES_ESTOQUE
-- =============================================================================
CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    produto_id          INT             NOT NULL,
    usuario_id          INT             NOT NULL,
    nota_entrada_id     INT             DEFAULT NULL,
    tipo                ENUM('entrada', 'saida', 'ajuste', 'venda', 'devolucao', 'nfe_entrada')
                                        NOT NULL,
    quantidade          DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    estoque_anterior    DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    estoque_posterior   DECIMAL(12,3)   NOT NULL DEFAULT 0.000,
    observacao          VARCHAR(255)    DEFAULT NULL,
    criado_em           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mov_estoque_produto
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_mov_estoque_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_mov_estoque_nota_entrada
        FOREIGN KEY (nota_entrada_id) REFERENCES notas_entrada(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    INDEX idx_mov_estoque_produto (produto_id),
    INDEX idx_mov_estoque_usuario (usuario_id),
    INDEX idx_mov_estoque_tipo (tipo),
    INDEX idx_mov_estoque_criado (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 12. MOVIMENTACOES_CAIXA
-- =============================================================================
CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    turno_id        INT             NOT NULL,
    usuario_id      INT             NOT NULL,
    tipo            ENUM('sangria', 'suprimento') NOT NULL,
    valor           DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    motivo          VARCHAR(255)    DEFAULT NULL,
    criado_em       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mov_caixa_turno
        FOREIGN KEY (turno_id) REFERENCES turnos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_mov_caixa_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_mov_caixa_turno (turno_id),
    INDEX idx_mov_caixa_usuario (usuario_id),
    INDEX idx_mov_caixa_tipo (tipo),
    INDEX idx_mov_caixa_criado (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 13. CONFIGURACOES
-- =============================================================================
CREATE TABLE IF NOT EXISTS configuracoes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    chave           VARCHAR(100)    NOT NULL UNIQUE,
    valor           TEXT            DEFAULT NULL,
    grupo           VARCHAR(50)     NOT NULL DEFAULT 'sistema',
    descricao       VARCHAR(255)    DEFAULT NULL,
    atualizado_em   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_configuracoes_chave (chave),
    INDEX idx_configuracoes_grupo (grupo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
