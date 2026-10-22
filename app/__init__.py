import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "gestaobar-chave-desenvolvimento"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gestaobar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
@login_manager.user_loader

def carregar_usuario(usuario_id):
    from app.models.models import Usuario
    return db.session.get(Usuario, int(usuario_id))

from app import models
from app import routes

from app.models.models import Estabelecimento, Usuario

with app.app_context():
    db.create_all()

    admin_usuario = os.environ.get("ADMIN_USERNAME")
    admin_senha = os.environ.get("ADMIN_PASSWORD")
    admin_nome = os.environ.get("ADMIN_NAME")
    admin_celular = os.environ.get("ADMIN_PHONE")
    admin_email = os.environ.get("ADMIN_EMAIL")

    if all([
        admin_usuario,
        admin_senha,
        admin_nome,
        admin_celular,
        admin_email
    ]):
        administrador_ativo = Usuario.query.filter_by(
            perfil="administrador",
            status="ativo"
        ).first()

        if not administrador_ativo:
            usuario_existente = Usuario.query.filter_by(
                usuario=admin_usuario
            ).first()

            email_existente = Usuario.query.filter_by(
                email=admin_email.lower()
            ).first()

            if not usuario_existente and not email_existente:
                estabelecimento = Estabelecimento.query.first()

                if not estabelecimento:
                    estabelecimento = Estabelecimento(
                        nome="Bar do Coelho"
                    )
                    db.session.add(estabelecimento)
                    db.session.flush()

                administrador = Usuario(
                    nome=admin_nome,
                    celular=admin_celular,
                    email=admin_email.lower(),
                    usuario=admin_usuario,
                    senha_hash=generate_password_hash(admin_senha),
                    perfil="administrador",
                    status="ativo",
                    estabelecimento_id=estabelecimento.id
                )

                db.session.add(administrador)
                db.session.commit()

                print("Administrador inicial criado com sucesso.")
            else:
                print(
                    "Administrador inicial não criado: "
                    "o usuário ou e-mail já existe."
                )