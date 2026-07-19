"""
Model de Pedido — acesso a dados de `pedidos` e `itens_pedido`.
Listagens usam JOIN em vez de N+1 queries por item/produto.
"""
from models.database import get_db
from models import produto_model


def criar(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()

    total = 0
    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        cursor.execute(
            """INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
               VALUES (?, ?, ?, ?)""",
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
        )
        produto_model.decrementar_estoque(item["produto_id"], item["quantidade"])

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def _agrupar_pedidos_com_itens(rows_pedidos, rows_itens):
    itens_por_pedido = {}
    for item in rows_itens:
        itens_por_pedido.setdefault(item["pedido_id"], []).append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] or "Desconhecido",
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    pedidos = []
    for row in rows_pedidos:
        pedidos.append({
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": itens_por_pedido.get(row["id"], []),
        })
    return pedidos


_ITENS_JOIN_QUERY = """
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
    FROM itens_pedido i
    LEFT JOIN produtos p ON p.id = i.produto_id
"""


def get_por_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    rows_pedidos = cursor.fetchall()

    cursor.execute(
        _ITENS_JOIN_QUERY + " WHERE i.pedido_id IN "
        "(SELECT id FROM pedidos WHERE usuario_id = ?)",
        (usuario_id,),
    )
    rows_itens = cursor.fetchall()

    return _agrupar_pedidos_com_itens(rows_pedidos, rows_itens)


def get_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    rows_pedidos = cursor.fetchall()

    cursor.execute(_ITENS_JOIN_QUERY)
    rows_itens = cursor.fetchall()

    return _agrupar_pedidos_com_itens(rows_pedidos, rows_itens)


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0] or 0

    cursor.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status")
    contagem_por_status = {status: count for status, count in cursor.fetchall()}

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": contagem_por_status.get("pendente", 0),
        "pedidos_aprovados": contagem_por_status.get("aprovado", 0),
        "pedidos_cancelados": contagem_por_status.get("cancelado", 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
