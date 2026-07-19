"""
Controller administrativo.

NOTA DE SEGURANÇA (ver relatório de auditoria, finding CRITICAL "SQL Injection via endpoint
administrativo"): o endpoint original `/admin/query`, que executava SQL arbitrário recebido do
corpo da requisição, foi REMOVIDO nesta refatoração — não existe uso legítimo para esse tipo de
endpoint em uma API pública, e mantê-lo é uma falha de segurança inaceitável (permite leitura/
escrita/exclusão arbitrária no banco por qualquer cliente).

O endpoint `/admin/reset-db` foi mantido para preservar o contrato original da API, mas segue
sem autenticação — isso está documentado no relatório como um risco residual (HIGH) que exige uma
camada de autenticação/autorização dedicada em uma iteração futura, fora do escopo desta
refatoração de arquitetura MVC.
"""
from flask import jsonify

from models.database import get_db


def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
