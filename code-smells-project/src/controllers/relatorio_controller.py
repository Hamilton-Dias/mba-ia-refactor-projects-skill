"""Controller de Relatórios."""
from flask import jsonify

from models import pedido_model, produto_model, usuario_model
from models.database import get_db


def relatorio_vendas():
    relatorio = pedido_model.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200


def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": len(produto_model.get_todos()),
            "usuarios": len(usuario_model.get_todos()),
            "pedidos": len(pedido_model.get_todos()),
        },
        "versao": "2.0.0",
    }), 200
