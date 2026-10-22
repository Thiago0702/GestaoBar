import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


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

with app.app_context():
    db.create_all()