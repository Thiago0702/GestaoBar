from app import db
from flask_login import UserMixin


class Estabelecimento(db.Model):
    __tablename__ = "estabelecimentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)

    usuarios = db.relationship(
        "Usuario",
        backref="estabelecimento",
        lazy=True
    )


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)

    perfil = db.Column(
        db.String(30),
        nullable=False,
        default="funcionario"
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pendente"
    )

    estabelecimento_id = db.Column(
        db.Integer,
        db.ForeignKey("estabelecimentos.id"),
        nullable=False
    )
class Mercadoria(db.Model):
    __tablename__ = "mercadoria"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    categoria = db.Column(
        db.String(80),
        nullable=False
    )

    preco_custo = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    preco_venda = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    estoque_minimo = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
class Venda(db.Model):
    __tablename__ = "vendas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    data_hora = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now()
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    taxa_entrega = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    forma_pagamento = db.Column(
        db.String(20),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="recebido"
    )

    tipo_pedido = db.Column(
    db.String(20),
    nullable=False,
    default="mesa"
    )

    mesa = db.Column(
    db.String(20),
    nullable=True
    )

    numero_pedido = db.Column(
    db.Integer,
    unique=True,
    nullable=True
    )

    cliente_nome = db.Column(
    db.String(150),
    nullable=True
    )

    cliente_telefone = db.Column(
    db.String(20),
    nullable=True
    )

    cliente_endereco = db.Column(
    db.String(200),
    nullable=True
    )

    cliente_numero = db.Column(
    db.String(20),
    nullable=True
    )

    cliente_complemento = db.Column(
    db.String(100),
    nullable=True
    )

    cliente_bairro = db.Column(
    db.String(100),
    nullable=True
    )

    cliente_cep = db.Column(
    db.String(10),
    nullable=True
    )

    usuario = db.relationship(
        "Usuario",
        backref="vendas"
    )

    itens = db.relationship(
        "ItemVenda",
        backref="venda",
        lazy=True,
        cascade="all, delete-orphan"
    )

class ItemVenda(db.Model):
    __tablename__ = "itens_venda"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    venda_id = db.Column(
        db.Integer,
        db.ForeignKey("vendas.id"),
        nullable=False
    )

    mercadoria_id = db.Column(
        db.Integer,
        db.ForeignKey("mercadoria.id"),
        nullable=False
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False
    )

    preco_unitario = db.Column(
        db.Float,
        nullable=False
    )

    subtotal = db.Column(
        db.Float,
        nullable=False
    )

    mercadoria = db.relationship(
        "Mercadoria",
        backref="itens_venda"
    )
