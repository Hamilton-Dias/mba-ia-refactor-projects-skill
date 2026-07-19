"""
Model de Usuário — acesso a dados da tabela `usuarios`.
Senhas nunca são armazenadas nem retornadas em texto puro (ver werkzeug.security).
"""
from werkzeug.security import generate_password_hash, check_password_hash

from models.database import get_db


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def get_por_email_com_senha(email):
    """Uso interno apenas para autenticação — inclui o hash da senha."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone()


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email, senha):
    row = get_por_email_com_senha(email)
    if row and check_password_hash(row["senha_hash"], senha):
        return _row_to_dict(row)
    return None
