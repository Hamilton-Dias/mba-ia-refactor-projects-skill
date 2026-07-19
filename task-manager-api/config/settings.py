"""
Configuração central da aplicação. Nenhum outro módulo deve conter segredos/credenciais
literais — tudo passa por aqui, lido de variáveis de ambiente, com defaults seguros apenas
para desenvolvimento local.
"""
import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))

    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "dev-only@example.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "dev-only-change-me")
