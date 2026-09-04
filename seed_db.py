import random
from datetime import datetime, timedelta
from database.connection import get_connection

def seed():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("Iniciando geração de dados fakes...")
    
    # 1. Obter usuário admin
    cursor.execute("SELECT id FROM usuarios LIMIT 1")
    user = cursor.fetchone()
    if not user:
        print("Crie um usuário primeiro!")
        return
    user_id = user['id']

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    cursor.execute("TRUNCATE TABLE venda_itens")
    cursor.execute("TRUNCATE TABLE vendas")
    cursor.execute("TRUNCATE TABLE pagamentos_venda")
    cursor.execute("TRUNCATE TABLE movimentacoes_caixa")
    cursor.execute("TRUNCATE TABLE turnos")
    cursor.execute("DELETE FROM movimentacoes_estoque WHERE observacao LIKE '%Fake%'")
    cursor.execute("DELETE FROM produtos WHERE codigo_interno LIKE 'FK%'")
    
    # 2. Criar Produtos
    produtos_fakes = [
        ("Cabo USB-C Rápido", 15.00, 35.00, 100),
        ("Carregador Turbo 20W", 25.00, 60.00, 50),
        ("Fone de Ouvido Bluetooth", 45.00, 120.00, 30),
        ("Película de Vidro 3D", 5.00, 20.00, 200),
        ("Capa Transparente Anti-Impacto", 8.00, 25.00, 150),
        ("Pop Socket Divertido", 3.00, 15.00, 80),
        ("Caderno Universitário 10 Matérias", 12.00, 28.00, 40),
        ("Caneta Esferográfica Azul", 0.50, 2.00, 500),
        ("Mochila Reforçada", 60.00, 150.00, 15),
        ("Mouse Sem Fio", 20.00, 55.00, 25)
    ]
    
    prod_ids = []
    for i, p in enumerate(produtos_fakes):
        codigo = f"FK{1000+i}"
        cursor.execute("""
            INSERT INTO produtos (codigo_interno, nome, preco_custo, preco_venda, estoque_atual, estoque_minimo, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (codigo, p[0], p[1], p[2], p[3], 10))
        prod_id = cursor.lastrowid
        prod_ids.append((prod_id, p[2])) # id, preco_venda
        
        cursor.execute("""
            INSERT INTO movimentacoes_estoque (produto_id, usuario_id, tipo, quantidade, estoque_anterior, estoque_posterior, observacao)
            VALUES (%s, %s, 'entrada', %s, 0, %s, 'Inventário Inicial Fake')
        """, (prod_id, user_id, p[3], p[3]))

    # 3. Gerar Vendas e Turnos (Caixas)
    today = datetime.now()
    total_vendas_geradas = 0
    
    for day_offset in range(30, -1, -1):
        data_atual = today - timedelta(days=day_offset)
        
        if data_atual.weekday() == 6:
            continue
            
        data_abertura = data_atual.replace(hour=8, minute=0, second=0)
        cursor.execute("""
            INSERT INTO turnos (usuario_id, valor_abertura, status, abertura)
            VALUES (%s, 100.00, 'aberto', %s)
        """, (user_id, data_abertura))
        turno_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO movimentacoes_caixa (turno_id, usuario_id, tipo, valor, motivo, criado_em)
            VALUES (%s, %s, 'suprimento', 100.00, 'Troco inicial', %s)
        """, (turno_id, user_id, data_abertura))
        
        qtd_vendas = random.randint(5, 15)
        total_vendas_dia = 0.0
        
        for v in range(qtd_vendas):
            hora_venda = data_abertura + timedelta(minutes=random.randint(30, 580))
            forma_pgto = random.choice(['dinheiro', 'pix', 'cartao_credito', 'cartao_debito'])
            
            cursor.execute("""
                INSERT INTO vendas (turno_id, usuario_id, subtotal, desconto, total, valor_recebido, troco, status, criado_em)
                VALUES (%s, %s, 0, 0, 0, 0, 0, 'finalizada', %s)
            """, (turno_id, user_id, hora_venda))
            venda_id = cursor.lastrowid
            total_vendas_geradas += 1
            
            qtd_itens = random.randint(1, 3)
            itens_venda = random.sample(prod_ids, qtd_itens)
            
            total_venda = 0
            for prod in itens_venda:
                p_id, p_preco = prod
                qtd_comprada = random.randint(1, 2)
                subtotal = qtd_comprada * p_preco
                total_venda += subtotal
                
                cursor.execute("""
                    INSERT INTO venda_itens (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (venda_id, p_id, qtd_comprada, p_preco, subtotal))
                
                cursor.execute("UPDATE produtos SET estoque_atual = estoque_atual - %s WHERE id = %s", (qtd_comprada, p_id))
            
            cursor.execute("""
                UPDATE vendas SET subtotal = %s, total = %s, valor_recebido = %s 
                WHERE id = %s
            """, (total_venda, total_venda, total_venda, venda_id))
            
            # Adiciona pagamento
            cursor.execute("""
                INSERT INTO pagamentos_venda (venda_id, forma, valor)
                VALUES (%s, %s, %s)
            """, (venda_id, forma_pgto, total_venda))
            
            total_vendas_dia += float(total_venda)

        data_fechamento = data_atual.replace(hour=18, minute=0, second=0)
        valor_final = 100.00 + total_vendas_dia
        
        cursor.execute("""
            UPDATE turnos 
            SET status = 'fechado', 
                valor_fechamento = %s, 
                total_vendas = %s, 
                total_suprimentos = 100.00,
                qtd_vendas = %s,
                fechamento = %s
            WHERE id = %s
        """, (valor_final, total_vendas_dia, qtd_vendas, data_fechamento, turno_id))
        
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Massa de dados gerada com sucesso! Total de Vendas Criadas: {total_vendas_geradas}")

if __name__ == '__main__':
    seed()
