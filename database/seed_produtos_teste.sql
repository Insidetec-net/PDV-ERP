-- =============================================================================
-- Sistema Meu Bazar — Produtos de Teste
-- =============================================================================

USE sistema_meu_bazar;

-- =============================================================================
-- Categorias (se não existirem)
-- =============================================================================
INSERT IGNORE INTO categorias (nome, descricao) VALUES
    ('Roupas Femininas', 'Blusas, vestidos, saias, calças femininas'),
    ('Roupas Masculinas', 'Camisas, calças, bermudas masculinas'),
    ('Roupas Infantis', 'Roupas para crianças e bebês'),
    ('Calçados', 'Sapatos, tênis, sandálias, chinelos'),
    ('Acessórios', 'Bolsas, cintos, carteiras, bijuterias'),
    ('Eletrônicos', 'Fones, carregadores, capas, acessórios eletrônicos'),
    ('Casa e Decoração', 'Utensílios domésticos, decoração, organização'),
    ('Brinquedos', 'Brinquedos e jogos diversos'),
    ('Cosméticos', 'Perfumes, maquiagem, cuidados pessoais'),
    ('Diversos', 'Produtos não categorizados');

-- =============================================================================
-- Produtos de Teste
-- =============================================================================

-- Roupas Femininas (categoria_id = 1)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000100011', 'MB-000001', 'Blusa Floral Rosa', 'Blusa feminina estampada floral rosa, tamanho M', 1, 25.00, 59.90, 58.48, '6106.10.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891000100028', 'MB-000002', 'Vestido Midi Azul', 'Vestido midi azul marinho com cinto, tamanho G', 1, 45.00, 119.90, 62.47, '6204.42.00', '00', '01', '01', 18.00, '5102', 'UN', 8, 3, TRUE),
    ('7891000100035', 'MB-000003', 'Calça Jeans Skinny', 'Calça jeans skinny feminina com elastano, tamanho 40', 1, 35.00, 89.90, 61.07, '6204.62.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 5, TRUE),
    ('7891000100042', 'MB-000004', 'Saia Plissada Preta', 'Saia plissada preta midi, tamanho M', 1, 28.00, 69.90, 59.93, '6204.52.00', '00', '01', '01', 18.00, '5102', 'UN', 12, 4, TRUE),
    ('7891000100059', 'MB-000005', 'Camiseta Básica Branca', 'Camiseta básica branca 100% algodão, tamanho P', 1, 12.00, 29.90, 59.83, '6109.10.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE);

-- Roupas Masculinas (categoria_id = 2)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000200018', 'MB-000006', 'Camisa Social Azul', 'Camisa social azul clara manga longa, tamanho G', 2, 40.00, 99.90, 59.94, '6205.20.00', '00', '01', '01', 18.00, '5102', 'UN', 10, 3, TRUE),
    ('7891000200025', 'MB-000007', 'Calça Jeans Masculina', 'Calça jeans masculina reta, tamanho 44', 2, 38.00, 94.90, 59.96, '6203.42.00', '00', '01', '01', 18.00, '5102', 'UN', 18, 5, TRUE),
    ('7891000200032', 'MB-000008', 'Bermuda Cargo Verde', 'Bermuda cargo verde oliva com bolsos, tamanho M', 2, 22.00, 54.90, 59.91, '6203.42.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE),
    ('7891000200049', 'MB-000009', 'Polo Listrada Preta', 'Camiseta polo listrada preta e branca, tamanho GG', 2, 25.00, 64.90, 61.39, '6105.10.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891000200056', 'MB-000010', 'Jaqueta Jeans Destroyed', 'Jaqueta jeans destroyed com forro, tamanho G', 2, 55.00, 139.90, 60.68, '6201.92.00', '00', '01', '01', 18.00, '5102', 'UN', 6, 2, TRUE);

-- Roupas Infantis (categoria_id = 3)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000300015', 'MB-000011', 'Vestido Infantil Floral', 'Vestido infantil floral para menina, tamanho 4', 3, 18.00, 44.90, 59.91, '6204.42.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891000300022', 'MB-000012', 'Conjunto Bebê Menino', 'Conjunto body + calça bebê menino 0-3 meses', 3, 15.00, 39.90, 62.41, '6111.20.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE),
    ('7891000300039', 'MB-000013', 'Camiseta Herói Azul', 'Camiseta infantil herói azul, tamanho 8', 3, 10.00, 24.90, 59.76, '6109.10.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE),
    ('7891000300046', 'MB-000014', 'Calça Legging Infantil', 'Calça legging infantil estampada, tamanho 6', 3, 12.00, 29.90, 59.83, '6204.62.00', '00', '01', '01', 18.00, '5102', 'UN', 22, 7, TRUE),
    ('7891000300053', 'MB-000015', 'Jaqueta Infantil Rosa', 'Jaqueta infantil rosa com capuz, tamanho 2', 3, 20.00, 49.90, 59.90, '6201.92.00', '00', '01', '01', 18.00, '5102', 'UN', 10, 3, TRUE);

-- Calçados (categoria_id = 4)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000400012', 'MB-000016', 'Tênis Esportivo Preto', 'Tênis esportivo preto unissex, tamanho 38', 4, 60.00, 149.90, 59.96, '6404.11.00', '00', '01', '01', 18.00, '5102', 'PAR', 12, 4, TRUE),
    ('7891000400029', 'MB-000017', 'Sandália Rasteira Rosa', 'Sandália rasteira rosa com tiras, tamanho 37', 4, 18.00, 44.90, 59.91, '6402.20.00', '00', '01', '01', 18.00, '5102', 'PAR', 20, 6, TRUE),
    ('7891000400036', 'MB-000018', 'Sapato Social Marrom', 'Sapato social marrom couro sintético, tamanho 40', 4, 50.00, 129.90, 61.51, '6405.10.00', '00', '01', '01', 18.00, '5102', 'PAR', 8, 2, TRUE),
    ('7891000400043', 'MB-000019', 'Chinelo Slide Branco', 'Chinelo slide branco com logo, tamanho 39', 4, 8.00, 19.90, 59.80, '6402.20.00', '00', '01', '01', 18.00, '5102', 'PAR', 40, 12, TRUE),
    ('7891000400050', 'MB-000020', 'Bota Cano Médio Preta', 'Bota cano médio preta com zíper, tamanho 38', 4, 70.00, 179.90, 61.06, '6403.51.00', '00', '01', '01', 18.00, '5102', 'PAR', 5, 2, TRUE);

-- Acessórios (categoria_id = 5)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000500019', 'MB-000021', 'Bolsa Tote Preta', 'Bolsa tote preta couro sintético, médio', 5, 35.00, 89.90, 61.07, '4202.22.00', '00', '01', '01', 18.00, '5102', 'UN', 10, 3, TRUE),
    ('7891000500026', 'MB-000022', 'Cinto Couro Marrom', 'Cinto masculino couro marrom com fivela dourada', 5, 15.00, 39.90, 62.41, '4203.30.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE),
    ('7891000500033', 'MB-000023', 'Carteira Feminina Rosa', 'Carteira feminina rosa com fecho magnético', 5, 12.00, 34.90, 65.59, '4202.31.00', '00', '01', '01', 18.00, '5102', 'UN', 18, 5, TRUE),
    ('7891000500040', 'MB-000024', 'Colar Pérola Falsa', 'Colar de pérolas falsas dourado, 45cm', 5, 8.00, 24.90, 67.87, '7117.90.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE),
    ('7891000500057', 'MB-000025', 'Óculos de Sol Aviador', 'Óculos de sol aviador com proteção UV400', 5, 20.00, 59.90, 66.61, '9004.10.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE);

-- Eletrônicos (categoria_id = 6)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000600016', 'MB-000026', 'Fone Bluetooth TWS', 'Fone de ouvido bluetooth TWS com case', 6, 45.00, 119.90, 62.47, '8518.30.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891000600023', 'MB-000027', 'Carregador Turbo USB-C', 'Carregador rápido turbo USB-C 20W', 6, 18.00, 49.90, 63.97, '8504.40.00', '00', '01', '01', 18.00, '5102', 'UN', 35, 10, TRUE),
    ('7891000600030', 'MB-000028', 'Capa iPhone 14 Clear', 'Capa transparente anti-impacto iPhone 14', 6, 8.00, 24.90, 67.87, '3926.90.00', '00', '01', '01', 18.00, '5102', 'UN', 50, 15, TRUE),
    ('7891000600047', 'MB-000029', 'Cabo USB-C 2m', 'Cabo USB-C para USB-C 2m nylon trançado', 6, 10.00, 29.90, 66.56, '8544.42.00', '00', '01', '01', 18.00, '5102', 'UN', 40, 12, TRUE),
    ('7891000600054', 'MB-000030', 'Power Bank 10000mAh', 'Power bank portátil 10000mAh com LED', 6, 35.00, 89.90, 61.07, '8507.60.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE);

-- Casa e Decoração (categoria_id = 7)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000700013', 'MB-000031', 'Vaso Cerâmica Branco', 'Vaso de cerâmica branco fosco, 15cm', 7, 12.00, 34.90, 65.59, '6913.10.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE),
    ('7891000700020', 'MB-000032', 'Almofada Decorativa', 'Almofada decorativa 45x45cm com enchimento', 7, 15.00, 39.90, 62.41, '9404.90.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891000700037', 'MB-000033', 'Quadro Abstrato 30x40', 'Quadro abstrato moderno 30x40cm com moldura', 7, 25.00, 69.90, 64.20, '9701.10.00', '00', '01', '01', 18.00, '5102', 'UN', 10, 3, TRUE),
    ('7891000700044', 'MB-000034', 'Organizador Bambu', 'Organizador de gavetas em bambu, 3 divisórias', 7, 18.00, 49.90, 63.97, '4419.12.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891000700051', 'MB-000035', 'Velas Aromáticas Kit 3', 'Kit 3 velas aromáticas lavanda, 150g cada', 7, 20.00, 54.90, 63.58, '3406.00.00', '00', '01', '01', 18.00, '5102', 'KIT', 18, 6, TRUE);

-- Brinquedos (categoria_id = 8)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000800010', 'MB-000036', 'Boneca Fashion 40cm', 'Boneca fashion 40cm com acessórios', 8, 25.00, 64.90, 61.40, '9503.00.00', '00', '01', '01', 18.00, '5102', 'UN', 12, 4, TRUE),
    ('7891000800027', 'MB-000037', 'Carrinho Controle Remoto', 'Carrinho de controle remoto 1:24', 8, 30.00, 79.90, 62.42, '9503.00.00', '00', '01', '01', 18.00, '5102', 'UN', 10, 3, TRUE),
    ('7891000800034', 'MB-000038', 'Blocos Montar 500pcs', 'Blocos de montar 500 peças compatível', 8, 20.00, 54.90, 63.58, '9503.00.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891000800041', 'MB-000039', 'Pelúciao Urso 30cm', 'Pelúcio urso marrom 30cm macio', 8, 18.00, 44.90, 59.91, '9503.00.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891000800058', 'MB-000040', 'Jogo Memória 40pcs', 'Jogo da memória educativo 40 peças', 8, 10.00, 29.90, 66.56, '9503.00.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE);

-- Cosméticos (categoria_id = 9)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000900017', 'MB-000041', 'Perfume Floral 50ml', 'Perfume feminino floral 50ml EDP', 9, 35.00, 89.90, 61.07, '3303.00.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891000900024', 'MB-000042', 'Batom Matte Vermelho', 'Batom matte vermelho intenso longa duração', 9, 12.00, 34.90, 65.59, '3304.10.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE),
    ('7891000900031', 'MB-000043', 'Hidratante Corporal 200ml', 'Hidratante corporal manteiga de karité', 9, 8.00, 24.90, 67.87, '3304.99.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE),
    ('7891000900048', 'MB-000044', 'Kit Skincare 3 Passos', 'Kit skincare limpeza+tônico+hidratante', 9, 25.00, 69.90, 64.24, '3304.99.00', '00', '01', '01', 18.00, '5102', 'KIT', 12, 4, TRUE),
    ('7891000900055', 'MB-000045', 'Protetor Solar FPS 50', 'Protetor solar facial FPS 50 50ml', 9, 15.00, 44.90, 66.62, '3304.99.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE);

-- Diversos (categoria_id = 10)
INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891001000014', 'MB-000046', 'Caneca Personalizada', 'Caneca cerâmica personalizada 325ml', 10, 8.00, 24.90, 67.87, '6912.00.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE),
    ('7891001000021', 'MB-000047', 'Chaveiro Couro', 'Chaveiro couro sintético com mosquetão', 10, 5.00, 14.90, 66.44, '8302.50.00', '00', '01', '01', 18.00, '5102', 'UN', 50, 15, TRUE),
    ('7891001000038', 'MB-000048', 'Agenda 2025 Capa Dura', 'Agenda 2025 capa dura 100 folhas', 10, 10.00, 29.90, 66.56, '4820.10.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891001000045', 'MB-000049', 'Garrafa Térmica 500ml', 'Garrafa térmica inox 500ml com canudo', 10, 18.00, 49.90, 63.97, '9617.00.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891001000052', 'MB-000050', 'Guarda-Chuva Automático', 'Guarda-chuva automático com estampa', 10, 12.00, 34.90, 65.59, '6601.91.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE);

-- =============================================================================
-- Atualizar contador de código interno
-- =============================================================================
UPDATE configuracoes SET valor = '50' WHERE chave = 'sistema_codigo_interno_contador';
