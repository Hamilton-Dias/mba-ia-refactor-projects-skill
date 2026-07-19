"""
Composition root — monta a aplicação Flask: carrega config, inicializa banco, registra
middlewares e blueprints. Nenhuma lógica de negócio deve viver aqui.
"""
import datetime

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from middlewares.error_handler import register_error_handlers

app = Flask(__name__)
app.config.from_object(Settings)

CORS(app)
db.init_app(app)

register_error_handlers(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)


@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}


@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '2.0'}


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
