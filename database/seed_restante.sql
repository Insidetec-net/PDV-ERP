-- Continuação - Cosméticos e Diversos
USE sistema_meu_bazar;

INSERT INTO produtos (codigo_barras, codigo_interno, nome, descricao, categoria_id, preco_custo, preco_venda, margem_lucro, ncm, cst_icms, cst_pis, cst_cofins, aliquota_icms, cfop, unidade, estoque_atual, estoque_minimo, ativo) VALUES
    ('7891000900017', 'MB-000041', 'Perfume Floral 50ml', 'Perfume feminino floral 50ml EDP', 9, 35.00, 89.90, 61.07, '3303.00.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891000900024', 'MB-000042', 'Batom Matte Vermelho', 'Batom matte vermelho intenso longa duração', 9, 12.00, 34.90, 65.59, '3304.10.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE),
    ('7891000900031', 'MB-000043', 'Hidratante Corporal 200ml', 'Hidratante corporal manteiga de karité', 9, 8.00, 24.90, 67.87, '3304.99.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE),
    ('7891000900048', 'MB-000044', 'Kit Skincare 3 Passos', 'Kit skincare limpeza+tônico+hidratante', 9, 25.00, 69.90, 64.24, '3304.99.00', '00', '01', '01', 18.00, '5102', 'KIT', 12, 4, TRUE),
    ('7891000900055', 'MB-000045', 'Protetor Solar FPS 50', 'Protetor solar facial FPS 50 50ml', 9, 15.00, 44.90, 66.62, '3304.99.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891001000014', 'MB-000046', 'Caneca Personalizada', 'Caneca cerâmica personalizada 325ml', 10, 8.00, 24.90, 67.87, '6912.00.00', '00', '01', '01', 18.00, '5102', 'UN', 30, 10, TRUE),
    ('7891001000021', 'MB-000047', 'Chaveiro Couro', 'Chaveiro couro sintético com mosquetão', 10, 5.00, 14.90, 66.44, '8302.50.00', '00', '01', '01', 18.00, '5102', 'UN', 50, 15, TRUE),
    ('7891001000038', 'MB-000048', 'Agenda 2025 Capa Dura', 'Agenda 2025 capa dura 100 folhas', 10, 10.00, 29.90, 66.56, '4820.10.00', '00', '01', '01', 18.00, '5102', 'UN', 20, 6, TRUE),
    ('7891001000045', 'MB-000049', 'Garrafa Térmica 500ml', 'Garrafa térmica inox 500ml com canudo', 10, 18.00, 49.90, 63.97, '9617.00.00', '00', '01', '01', 18.00, '5102', 'UN', 15, 5, TRUE),
    ('7891001000052', 'MB-000050', 'Guarda-Chuva Automático', 'Guarda-chuva automático com estampa', 10, 12.00, 34.90, 65.59, '6601.91.00', '00', '01', '01', 18.00, '5102', 'UN', 25, 8, TRUE)
ON DUPLICATE KEY UPDATE nome = VALUES(nome);

-- Atualizar contador de código interno
UPDATE configuracoes SET valor = '50' WHERE chave = 'sistema_codigo_interno_contador';
