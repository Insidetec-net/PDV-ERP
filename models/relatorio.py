"""
Model de Relatórios — Agregações, Curva ABC, Fluxo de Caixa.
"""

from database.connection import get_connection

class RelatorioModel:
    def get_vendas_por_periodo(self, start_date: str, end_date: str):
        """Retorna vendas por dia num período."""
        try:
            conn = get_connection()
            if not conn: return []
            cursor = conn.cursor(dictionary=True)
            
            # Formato esperado start_date, end_date: 'YYYY-MM-DD'
            query = """
                SELECT 
                    DATE(criado_em) as data,
                    COUNT(id) as total_vendas,
                    SUM(total) as receita_total
                FROM vendas
                WHERE status = 'finalizada' 
                  AND DATE(criado_em) BETWEEN %s AND %s
                GROUP BY DATE(criado_em)
                ORDER BY data ASC
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Erro ao obter vendas por período: {e}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def get_curva_abc(self, start_date: str, end_date: str):
        """Retorna produtos mais vendidos e faturamento gerado."""
        try:
            conn = get_connection()
            if not conn: return []
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    p.codigo_interno,
                    p.nome,
                    SUM(vi.quantidade) as qtd_vendida,
                    SUM(vi.subtotal) as receita_gerada
                FROM venda_itens vi
                JOIN vendas v ON vi.venda_id = v.id
                JOIN produtos p ON vi.produto_id = p.id
                WHERE v.status = 'finalizada'
                  AND DATE(v.criado_em) BETWEEN %s AND %s
                GROUP BY p.id
                ORDER BY receita_gerada DESC
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Erro ao obter curva ABC: {e}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def get_estoque_atual(self):
        """Retorna a posição atual do estoque e valor imobilizado."""
        try:
            conn = get_connection()
            if not conn: return []
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    codigo_interno,
                    nome,
                    estoque_atual,
                    preco_custo,
                    preco_venda,
                    (estoque_atual * preco_custo) as custo_imobilizado,
                    (estoque_atual * preco_venda) as receita_esperada
                FROM produtos
                WHERE ativo = 1 AND estoque_atual > 0
                ORDER BY custo_imobilizado DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Erro ao obter estoque atual: {e}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def get_movimentacoes_caixa(self, start_date: str, end_date: str):
        """Retorna todas as operações de caixa no período."""
        try:
            conn = get_connection()
            if not conn: return []
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    cm.criado_em as data_hora,
                    cm.tipo,
                    cm.valor,
                    cm.motivo as observacao,
                    u.nome as operador
                FROM movimentacoes_caixa cm
                JOIN turnos c ON cm.turno_id = c.id
                LEFT JOIN usuarios u ON cm.usuario_id = u.id
                WHERE DATE(cm.criado_em) BETWEEN %s AND %s
                ORDER BY cm.criado_em DESC
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Erro ao obter movimentos de caixa: {e}")
            return []
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
