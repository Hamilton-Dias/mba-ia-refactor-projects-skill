"""
Configuração central da aplicação.
Nenhum outro módulo deve conter segredos/credenciais literais — tudo passa por aqui,
lido de variáveis de ambiente, com defaults seguros apenas para desenvolvimento local.
"""
import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
