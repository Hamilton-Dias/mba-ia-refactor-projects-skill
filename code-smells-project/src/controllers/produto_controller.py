"""Controller de Produto — orquestra validação de negócio e chamadas ao model."""
from flask import request, jsonify

from models import produto_model

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


def listar_produtos():
    produtos = produto_model.get_todos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.get_por_id(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def _validar_produto(dados, parcial=False):
    if not parcial:
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                return f"{campo.capitalize()} é obrigatório"

    if "preco" in dados and dados["preco"] < 0:
        return "Preço não pode ser negativo"
    if "estoque" in dados and dados["estoque"] < 0:
        return "Estoque não pode ser negativo"
    if "nome" in dados:
        if len(dados["nome"]) < 2:
            return "Nome muito curto"
        if len(dados["nome"]) > 200:
            return "Nome muito longo"
    if "categoria" in dados and dados["categoria"] not in CATEGORIAS_VALIDAS:
        return f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}"
    return None


def criar_produto():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    erro = _validar_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_id = produto_model.criar(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = request.get_json()
    if not produto_model.get_por_id(id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    erro = _validar_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.atualizar(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    if not produto_model.get_por_id(id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    produto_model.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    preco_min = float(preco_min) if preco_min else None
    preco_max = float(preco_max) if preco_max else None

    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
