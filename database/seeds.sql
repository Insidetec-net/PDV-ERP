-- =============================================================================
-- Sistema Meu Bazar — Dados Iniciais (Seeds)
-- Execute após o schema.sql
-- =============================================================================

USE sistema_meu_bazar;

-- =============================================================================
-- Usuário Administrador Padrão
-- Login: admin | Senha: admin123 (hash bcrypt)
-- IMPORTANTE: Trocar a senha no primeiro acesso!
-- =============================================================================
INSERT INTO usuarios (nome, login, senha_hash, perfil, ativo) VALUES
    ('Administrador', 'admin', '$2b$12$LJ3m4ys3GZ5aKbHv8VH5eu8VdJb8K5VK5Av3RQ5DjGmY0vY3r0VGi', 'admin', TRUE)
ON DUPLICATE KEY UPDATE nome = VALUES(nome);


-- =============================================================================
-- Categorias Padrão
-- =============================================================================
INSERT INTO categorias (nome, descricao) VALUES
    ('Roupas Femininas', 'Blusas, vestidos, saias, calças femininas'),
    ('Roupas Masculinas', 'Camisas, calças, bermudas masculinas'),
    ('Roupas Infantis', 'Roupas para crianças e bebês'),
    ('Calçados', 'Sapatos, tênis, sandálias, chinelos'),
    ('Acessórios', 'Bolsas, cintos, carteiras, bijuterias'),
    ('Eletrônicos', 'Fones, carregadores, capas, acessórios eletrônicos'),
    ('Casa e Decoração', 'Utensílios domésticos, decoração, organização'),
    ('Brinquedos', 'Brinquedos e jogos diversos'),
    ('Cosméticos', 'Perfumes, maquiagem, cuidados pessoais'),
    ('Diversos', 'Produtos não categorizados')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);


-- =============================================================================
-- Configurações da Empresa (White-Label)
-- Todos os valores devem ser preenchidos no primeiro acesso via Módulo Config
-- =============================================================================
INSERT INTO configuracoes (chave, valor, grupo, descricao) VALUES
    -- Dados da Empresa
    ('empresa_razao_social',    '', 'empresa', 'Razão social da empresa'),
    ('empresa_nome_fantasia',   '', 'empresa', 'Nome fantasia'),
    ('empresa_cnpj',            '', 'empresa', 'CNPJ da empresa (XX.XXX.XXX/XXXX-XX)'),
    ('empresa_ie',              '', 'empresa', 'Inscrição Estadual'),
    ('empresa_im',              '', 'empresa', 'Inscrição Municipal'),
    ('empresa_endereco',        '', 'empresa', 'Endereço completo'),
    ('empresa_numero',          '', 'empresa', 'Número do endereço'),
    ('empresa_complemento',     '', 'empresa', 'Complemento do endereço'),
    ('empresa_bairro',          '', 'empresa', 'Bairro'),
    ('empresa_cidade',          '', 'empresa', 'Cidade'),
    ('empresa_uf',              '', 'empresa', 'UF (sigla do estado)'),
    ('empresa_cep',             '', 'empresa', 'CEP (XXXXX-XXX)'),
    ('empresa_telefone',        '', 'empresa', 'Telefone da empresa'),
    ('empresa_email',           '', 'empresa', 'E-mail da empresa'),
    ('empresa_logo_path',       '', 'empresa', 'Caminho da logo da empresa'),
    ('empresa_regime_tributario', '3', 'empresa', 'Regime tributário (1=Simples, 2=Simples Excesso, 3=Lucro Presumido)'),
    ('empresa_codigo_municipio', '', 'empresa', 'Código IBGE do município'),

    -- Configurações Fiscais
    ('fiscal_api_provider',     'focusnfe', 'fiscal', 'Provedor da API fiscal (focusnfe)'),
    ('fiscal_api_token',        '', 'fiscal', 'Token de autenticação da API fiscal'),
    ('fiscal_ambiente',         '2', 'fiscal', 'Ambiente fiscal (1=Produção, 2=Homologação)'),
    ('fiscal_serie_nfce',       '1', 'fiscal', 'Série da NFC-e'),
    ('fiscal_csc_id',           '', 'fiscal', 'ID do CSC (Código de Segurança do Contribuinte)'),
    ('fiscal_csc_token',        '', 'fiscal', 'Token CSC'),
    ('fiscal_aliquota_icms',    '18.00', 'fiscal', 'Alíquota padrão de ICMS (%)'),
    ('fiscal_aliquota_pis',     '0.65', 'fiscal', 'Alíquota de PIS (%)'),
    ('fiscal_aliquota_cofins',  '3.00', 'fiscal', 'Alíquota de COFINS (%)'),
    ('fiscal_cst_icms_padrao',  '00', 'fiscal', 'CST ICMS padrão para novos produtos'),
    ('fiscal_cst_pis_padrao',   '01', 'fiscal', 'CST PIS padrão para novos produtos'),
    ('fiscal_cst_cofins_padrao','01', 'fiscal', 'CST COFINS padrão para novos produtos'),
    ('fiscal_cfop_padrao',      '5102', 'fiscal', 'CFOP padrão para vendas'),

    -- Configurações de Impressão
    ('impressao_tipo',          'padrao', 'impressao', 'Tipo de impressão (padrao ou escpos)'),
    ('impressao_impressora',    '', 'impressao', 'Nome da impressora padrão'),
    ('impressao_largura_cupom', '80', 'impressao', 'Largura do cupom em mm (58 ou 80)'),

    -- Configurações do Sistema
    ('sistema_markup_padrao',   '100', 'sistema', 'Markup padrão para novos produtos (%)'),
    ('sistema_estoque_minimo',  '5', 'sistema', 'Estoque mínimo padrão para alertas'),
    ('sistema_backup_automatico', 'true', 'sistema', 'Habilitar backup automático diário'),
    ('sistema_backup_horario',  '23:00', 'sistema', 'Horário do backup automático'),
    ('sistema_tema',            'escuro', 'sistema', 'Tema visual (escuro ou claro)'),
    ('sistema_codigo_interno_contador', '0', 'sistema', 'Último número do código interno (MB-XXXXXX)')
ON DUPLICATE KEY UPDATE descricao = VALUES(descricao);
