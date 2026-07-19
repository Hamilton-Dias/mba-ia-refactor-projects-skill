"""
Composition root — monta a aplicação Flask: carrega config, inicializa banco,
registra middlewares e rotas. Nenhuma lógica de negócio deve viver aqui.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from models.database import get_db
from middlewares.error_handler import register_error_handlers
from views.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Settings)
    CORS(app)

    register_error_handlers(app)
    register_routes(app)

    return app


app = create_app()

if __name__ == "__main__":
    get_db()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{Settings.PORT}")
    print("=" * 50)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
