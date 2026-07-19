"""
Tratamento de erro centralizado — substitui os `try/except`/`except:` genéricos que existiam
espalhados pelas rotas originais, engolindo qualquer erro sem diferenciar validação de falha
interna.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({"error": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e):
        logger.exception("Erro não tratado")
        return jsonify({"error": "Erro interno do servidor"}), 500
