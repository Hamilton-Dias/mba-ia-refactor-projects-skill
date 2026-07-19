"""Controller de Pedido — orquestra criação/consulta de pedidos."""
import logging

from flask import request, jsonify

from models import pedido_model

logger = logging.getLogger(__name__)

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def _notificar_novo_pedido(pedido_id, usuario_id):
    # Simulação de disparo de notificações (e-mail/SMS/push). Em produção, isso chamaria
    # um serviço de notificação dedicado — mantido como log para fins de demonstração.
    logger.info("Notificação: pedido %s criado para usuário %s", pedido_id, usuario_id)


def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = pedido_model.criar(usuario_id, itens)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    _notificar_novo_pedido(resultado["pedido_id"], usuario_id)

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.get_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_model.get_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    pedido_model.atualizar_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("Notificação: pedido %s aprovado. Preparar envio.", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Notificação: pedido %s cancelado. Devolver estoque.", pedido_id)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
