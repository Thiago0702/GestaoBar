from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import update
from app import app, db
from app.models.models import Usuario, Mercadoria, Venda, ItemVenda
from werkzeug.security import check_password_hash, generate_password_hash
import unicodedata


def normalizar_bairro(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return " ".join(texto.casefold().strip().split())


FRETES_POR_BAIRRO = {
    normalizar_bairro("Giovane"): 9.00,
    normalizar_bairro("Pq Recreio"): 8.00,
    normalizar_bairro("Colônia"): 13.00,
    normalizar_bairro("Chác. Eldorado"): 6.00,
    normalizar_bairro("Sta. Fé"): 7.00,
    normalizar_bairro("Casa Coelho"): 6.00,
    normalizar_bairro("São Francisco"): 8.00,
    normalizar_bairro("Novo Parreleiros"): 6.00,
    normalizar_bairro("Parque Amazonas"): 6.00,
    normalizar_bairro("Hosp. Parreleiros"): 6.00,
    normalizar_bairro("Vargem Grande"): 11.00,
    normalizar_bairro("Jd. Silveira"): 9.00,
    normalizar_bairro("Álamos"): 8.00,
    normalizar_bairro("Aladim"): 8.00,
    normalizar_bairro("Padaria Troró"): 13.00,
    normalizar_bairro("Embura"): 20.00,
    normalizar_bairro("Jd. Fontes"): 20.00,
    normalizar_bairro("Novo América"): 20.00,
    normalizar_bairro("25º"): 6.00,
    normalizar_bairro("Pq. Florestal"): 16.00,
    normalizar_bairro("Vilela"): 15.00,
    normalizar_bairro("Recanto"): 17.00,
    normalizar_bairro("V. Marcelo"): 20.00,
    normalizar_bairro("São Norberto"): 13.00,
    normalizar_bairro("Papai Noel"): 13.00,
    normalizar_bairro("Vila Rochel"): 7.00,
    normalizar_bairro("Progresso"): 8.00,
    normalizar_bairro("Barragem"): 25.00,
    normalizar_bairro("Jusa"): 13.00,
    normalizar_bairro("Bosque Sol"): 7.00,
    normalizar_bairro("Fred"): 18.00,
}


@app.route("/")
@login_required
def inicio():

    from datetime import datetime

    data_selecionada = request.args.get("data")

    if data_selecionada:
        hoje = datetime.strptime(
            data_selecionada,
            "%Y-%m-%d"
        ).date()
    else:
        hoje = datetime.now().date()

    data_consulta = hoje.strftime("%d/%m/%Y")
    dias_semana = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo"
    ]

    dia_consulta = dias_semana[hoje.weekday()]


    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_hora) == hoje
    ).all()

    faturamento_hoje = sum(
        venda.total
        for venda in vendas_hoje
    )

    quantidade_vendas = len(vendas_hoje)

    pedidos_novos = Venda.query.filter_by(
        status="recebido"
    ).count()

    if quantidade_vendas > 0:
        ticket_medio = (
            faturamento_hoje / quantidade_vendas
        )
    else:
        ticket_medio = 0

    quantidade_produtos = Mercadoria.query.filter_by(
        ativo=True
    ).count()

    produtos_estoque_baixo = Mercadoria.query.filter(
        Mercadoria.ativo == True,
        Mercadoria.quantidade <= Mercadoria.estoque_minimo
    ).order_by(
        Mercadoria.quantidade.asc()
    ).all()

    perdas_hoje = db.session.execute(
        db.text(
            """
            SELECT COALESCE(
                SUM(perdas.quantidade * mercadoria.preco_custo),
                0
            )
            FROM perdas
            INNER JOIN mercadoria
                ON perdas.mercadoria_id = mercadoria.id
            WHERE date(perdas.data_hora) = :hoje
            """
        ),
        {"hoje": hoje}
    ).scalar()

    perdas_hoje = perdas_hoje or 0

    lucro_estimado = 0

    for venda in vendas_hoje:

        for item in venda.itens:

            produto = item.mercadoria

            lucro_item = (
                produto.preco_venda -
                produto.preco_custo
            ) * item.quantidade

            lucro_estimado += lucro_item

    return render_template(
        "index.html",
        faturamento_hoje=faturamento_hoje,
        quantidade_vendas=quantidade_vendas,
        ticket_medio=ticket_medio,
        quantidade_produtos=quantidade_produtos,
        lucro_estimado=lucro_estimado,
        perdas_hoje=perdas_hoje,
        pedidos_novos=pedidos_novos,
        produtos_estoque_baixo=produtos_estoque_baixo,
        data_consulta=data_consulta,
        dia_consulta=dia_consulta,
        data_selecionada=data_selecionada,
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        usuario_db = Usuario.query.filter_by(
            usuario=usuario,
            status="ativo"
        ).first()

        if usuario_db and check_password_hash(
            usuario_db.senha_hash,
            senha
        ):
            login_user(usuario_db)

            return redirect(url_for("inicio"))

        return render_template(
            "login.html",
            erro="Usuário ou senha inválidos."
        )

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        celular = request.form.get("celular", "").strip()
        email = request.form.get("email", "").strip().lower()
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not nome or not celular or not email or not usuario or not senha:
            return render_template(
                "cadastro.html",
                erro="Preencha todos os campos."
            )

        if senha != confirmar_senha:
            return render_template(
                "cadastro.html",
                erro="As senhas não são iguais."
            )

        if Usuario.query.filter_by(usuario=usuario).first():
            return render_template(
                "cadastro.html",
                erro="Este usuário já está cadastrado."
            )

        if Usuario.query.filter_by(email=email).first():
            return render_template(
                "cadastro.html",
                erro="Este e-mail já está cadastrado."
            )

        novo_usuario = Usuario(
            nome=nome,
            celular=celular,
            email=email,
            usuario=usuario,
            senha_hash=generate_password_hash(senha),
            perfil="funcionario",
            status="pendente",
            estabelecimento_id=1
        )

        db.session.add(novo_usuario)
        db.session.commit()

        return render_template(
            "login.html",
            sucesso=(
                "Cadastro realizado com sucesso! "
                "Aguarde a aprovação do administrador."
            )
        )

    return render_template("cadastro.html")

@app.route("/admin/funcionarios")
@login_required
def funcionarios():

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    funcionarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    return render_template(
        "funcionarios.html",
        funcionarios=funcionarios
    )
@app.route("/admin/funcionarios/<int:usuario_id>/aprovar", methods=["POST"])
@login_required
def aprovar_funcionario(usuario_id):

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    funcionario = Usuario.query.get_or_404(usuario_id)

    funcionario.status = "ativo"

    db.session.commit()

    return redirect(url_for("funcionarios"))

@app.route("/admin/funcionarios/<int:usuario_id>/recusar", methods=["POST"])
@login_required
def recusar_funcionario(usuario_id):

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    funcionario = Usuario.query.get_or_404(usuario_id)

    funcionario.status = "recusado"

    db.session.commit()

    return redirect(url_for("funcionarios"))

@app.route("/admin/funcionarios/<int:usuario_id>/bloquear", methods=["POST"])
@login_required
def bloquear_funcionario(usuario_id):

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    funcionario = Usuario.query.get_or_404(usuario_id)

    # Impede que o administrador bloqueie a própria conta
    if funcionario.id == current_user.id:
        return "Você não pode bloquear sua própria conta.", 400

    funcionario.status = "bloqueado"

    db.session.commit()

    return redirect(url_for("funcionarios"))

@app.route("/admin/funcionarios/<int:usuario_id>/reativar", methods=["POST"])
@login_required
def reativar_funcionario(usuario_id):

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    funcionario = Usuario.query.get_or_404(usuario_id)

    funcionario.status = "ativo"

    db.session.commit()

    return redirect(url_for("funcionarios"))

@app.route("/admin/mercadorias", methods=["GET", "POST"])
@login_required
def mercadorias():

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()

        preco_custo = request.form.get(
            "preco_custo",
            "0"
        )

        preco_venda = request.form.get(
            "preco_venda",
            "0"
        )

        quantidade = request.form.get(
            "quantidade",
            "0"
        )

        estoque_minimo = request.form.get(
            "estoque_minimo",
            "0"
        )

        if not nome or not categoria:
            return render_template(
                "mercadorias.html",
                erro="Preencha o nome e a categoria."
            )

        nova_mercadoria = Mercadoria(
            nome=nome,
            categoria=categoria,
            preco_custo=float(preco_custo),
            preco_venda=float(preco_venda),
            quantidade=int(quantidade),
            estoque_minimo=int(estoque_minimo),
            ativo=True
        )

        db.session.add(nova_mercadoria)
        db.session.commit()

        return redirect(
            url_for("mercadorias")
        )

    produtos = Mercadoria.query.order_by(
        Mercadoria.nome
    ).all()

    return render_template(
        "mercadorias.html",
        produtos=produtos
    )

@app.route("/buscar-produto")
@login_required
def buscar_produto():
    produtos = Mercadoria.query.order_by(
        Mercadoria.categoria,
        Mercadoria.nome
    ).all()

    return render_template(
        "buscar_produto.html",
        produtos=produtos
    )

@app.route("/admin/mercadorias/<int:produto_id>/editar", methods=["GET", "POST"])
@login_required
def editar_mercadoria(produto_id):

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    produto = Mercadoria.query.get_or_404(produto_id)

    if request.method == "POST":

        produto.nome = request.form.get("nome", "").strip()
        produto.categoria = request.form.get("categoria", "").strip()
        produto.preco_custo = float(
            request.form.get("preco_custo", 0)
        )
        produto.preco_venda = float(
            request.form.get("preco_venda", 0)
        )
        produto.quantidade = int(
            request.form.get("quantidade", 0)
        )
        produto.estoque_minimo = int(
            request.form.get("estoque_minimo", 0)
        )

        db.session.commit()

        return redirect(url_for("mercadorias"))

    return render_template(
        "editar_mercadoria.html",
        produto=produto
    )


@app.route("/admin/mercadorias/<int:produto_id>/excluir", methods=["POST"])
@login_required

def excluir_mercadoria(produto_id):

    if current_user.perfil != "administrador":
        return "Acesso não autorizado.", 403

    produto = Mercadoria.query.get_or_404(produto_id)

    db.session.delete(produto)
    db.session.commit()

    return redirect(url_for("mercadorias"))

@app.route("/vendas")
@login_required
def vendas():

    produtos = Mercadoria.query.filter_by(
        ativo=True
    ).order_by(
        Mercadoria.categoria,
        Mercadoria.nome
    ).all()

    return render_template(
        "vendas.html",
        produtos=produtos
    )
@app.route("/vendas/finalizar", methods=["POST"])
@login_required
def finalizar_venda():

    dados = request.get_json()

    if not dados or "itens" not in dados:
        return {
            "sucesso": False,
            "erro": "Nenhum item foi enviado."
        }, 400

    itens = dados["itens"]

    forma_pagamento = dados.get("forma_pagamento")

    if not itens:
        return {
            "sucesso": False,
            "erro": "O carrinho está vazio."
        }, 400

    total = 0
    itens_venda = []

    for item in itens:

        produto = Mercadoria.query.get(item["id"])

        if not produto:
            return {
                "sucesso": False,
                "erro": "Produto não encontrado."
            }, 404

        quantidade = int(item["quantidade"])

        if quantidade <= 0:
            return {
                "sucesso": False,
                "erro": "Quantidade inválida."
            }, 400

        if quantidade > produto.quantidade:
            return {
                "sucesso": False,
                "erro": (
                    f"Estoque insuficiente para "
                    f"{produto.nome}."
                )
            }, 400

        subtotal = produto.preco_venda * quantidade

        total += subtotal

        itens_venda.append({
            "produto": produto,
            "quantidade": quantidade,
            "preco": produto.preco_venda,
            "subtotal": subtotal
        })

    nova_venda = Venda(
        usuario_id=current_user.id,
        total=total,
        forma_pagamento=forma_pagamento
    )

    db.session.add(nova_venda)

    for item in itens_venda:

        produto = item["produto"]

        produto.quantidade -= item["quantidade"]

        novo_item = ItemVenda(
            venda=nova_venda,
            mercadoria_id=produto.id,
            quantidade=item["quantidade"],
            preco_unitario=item["preco"],
            subtotal=item["subtotal"]
        )

        db.session.add(novo_item)

    db.session.commit()

    return {
        "sucesso": True,
        "venda_id": nova_venda.id,
        "total": total
    }

@app.route("/vendas/historico")
@login_required
def historico_vendas():

    vendas = Venda.query.order_by(
        Venda.data_hora.desc()
    ).all()

    return render_template(
        "historico_vendas.html",
        vendas=vendas
    )

@app.route("/fechamento")
@login_required
def fechamento():

    from datetime import datetime

    data_selecionada = request.args.get("data")

    if data_selecionada:
        hoje = datetime.strptime(
            data_selecionada,
            "%Y-%m-%d"
        ).date()
    else:
        hoje = datetime.now().date()

    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_hora) == hoje
    ).all()

    dinheiro = sum(
        venda.total
        for venda in vendas_hoje
        if venda.forma_pagamento == "Dinheiro"
    )

    pix = sum(
        venda.total
        for venda in vendas_hoje
        if venda.forma_pagamento == "Pix"
    )

    debito = sum(
        venda.total
        for venda in vendas_hoje
        if venda.forma_pagamento == "Débito"
    )

    credito = sum(
        venda.total
        for venda in vendas_hoje
        if venda.forma_pagamento == "Crédito"
    )

    total_vendas = sum(
        venda.total
        for venda in vendas_hoje
    )

    quantidade_vendas = len(vendas_hoje)

    perdas_hoje = db.session.execute(
        db.text(
            """
            SELECT COALESCE(
                SUM(perdas.quantidade * mercadoria.preco_custo),
                0
            )
            FROM perdas
            INNER JOIN mercadoria
                ON perdas.mercadoria_id = mercadoria.id
            WHERE date(perdas.data_hora) = :hoje
            """
        ),
        {"hoje": hoje}
    ).scalar() or 0

    quantidade_perdas = db.session.execute(
    db.text(
        """
        SELECT COALESCE(
            SUM(perdas.quantidade),
            0
        )
        FROM perdas
        WHERE date(perdas.data_hora) = :hoje
        """
    ),
    {"hoje": hoje}
).scalar() or 0

    resultado_liquido = total_vendas - perdas_hoje

    return render_template(
        "fechamento.html",
        hoje=hoje,
        dinheiro=dinheiro,
        pix=pix,
        debito=debito,
        credito=credito,
        total_vendas=total_vendas,
        quantidade_vendas=quantidade_vendas,
        perdas_hoje=perdas_hoje,
        resultado_liquido=resultado_liquido,
        quantidade_perdas=quantidade_perdas,
    )
@app.route("/vendas/historico/<int:venda_id>")
@login_required
def detalhes_venda(venda_id):

    venda = Venda.query.get_or_404(venda_id)

    return render_template(
        "detalhes_venda.html",
        venda=venda
    )

def detalhes_venda(venda_id):

    venda = Venda.query.get_or_404(venda_id)

    return render_template(
        "detalhes_venda.html",
        venda=venda
    )

@app.route("/admin/perdas", methods=["GET", "POST"])
@login_required
def registrar_perda():

    if current_user.perfil != "administrador":
        return "Acesso negado", 403

    produtos = Mercadoria.query.filter_by(ativo=True).all()

    if request.method == "POST":

        mercadoria_id = int(request.form["mercadoria_id"])
        quantidade = int(request.form["quantidade"])
        motivo = request.form.get("motivo", "").strip()

        produto = Mercadoria.query.get_or_404(mercadoria_id)

        if quantidade > produto.quantidade:
            return "Quantidade de perda maior que o estoque disponível.", 400

        perda = db.session.execute(
            db.text(
                """
                INSERT INTO perdas
                (data_hora, usuario_id, mercadoria_id, quantidade, motivo)
                VALUES
                (CURRENT_TIMESTAMP, :usuario_id, :mercadoria_id,
                 :quantidade, :motivo)
                """
            ),
            {
                "usuario_id": current_user.id,
                "mercadoria_id": produto.id,
                "quantidade": quantidade,
                "motivo": motivo
            }
        )

        produto.quantidade -= quantidade

        db.session.commit()

        return redirect(url_for("registrar_perda"))

    return render_template(
        "registrar_perda.html",
        produtos=produtos
    )
@app.route("/admin/perdas/historico")
@login_required
def historico_perdas():

    if current_user.perfil != "administrador":
        return "Acesso negado", 403

    perdas = db.session.execute(
        db.text(
            """
            SELECT
                perdas.id,
                perdas.data_hora,
                mercadoria.nome AS produto,
                perdas.quantidade,
                perdas.motivo,
                mercadoria.preco_custo,
                usuarios.nome AS usuario
            FROM perdas
            INNER JOIN mercadoria
                ON perdas.mercadoria_id = mercadoria.id
            INNER JOIN usuarios
                ON perdas.usuario_id = usuarios.id
            ORDER BY perdas.data_hora DESC
            """
        )
    ).mappings().all()

    return render_template(
        "historico_perdas.html",
        perdas=perdas
    )
@app.route("/cardapio")
def cardapio():

    produtos = Mercadoria.query.filter_by(
        ativo=True
    ).order_by(
        Mercadoria.categoria,
        Mercadoria.nome
    ).all()

    return render_template(
        "cardapio.html",
        produtos=produtos
    )

@app.route("/cardapio/mesa/<int:mesa>")
def cardapio_mesa(mesa):

    produtos = Mercadoria.query.filter_by(
        ativo=True
    ).order_by(
        Mercadoria.categoria,
        Mercadoria.nome
    ).all()

    return render_template(
        "cardapio.html",
        produtos=produtos,
        mesa=mesa
    )

@app.route("/pedido/enviar", methods=["POST"])
def enviar_pedido():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return {"sucesso": False, "mensagem": "Dados do pedido inválidos."}, 400

    itens = dados.get("itens", [])
    mesa = dados.get("mesa")

    if not isinstance(itens, list) or not itens:
        return {"sucesso": False, "mensagem": "O pedido está vazio."}, 400

    if mesa is None or not str(mesa).strip():
        return {"sucesso": False, "mensagem": "Informe o número da mesa."}, 400

    try:
        # Validar todos os itens antes de registrar a venda.
        itens_validados = []
        total = 0

        for produto in itens:
            if not isinstance(produto, dict):
                return {"sucesso": False, "mensagem": "Item inválido."}, 400

            try:
                produto_id = int(produto.get("id"))
                quantidade = int(produto.get("quantidade"))
            except (TypeError, ValueError):
                return {"sucesso": False, "mensagem": "Produto ou quantidade inválidos."}, 400

            if produto_id <= 0 or quantidade <= 0:
                return {"sucesso": False, "mensagem": "A quantidade deve ser maior que zero."}, 400

            mercadoria = db.session.get(Mercadoria, produto_id)

            if not mercadoria:
                return {"sucesso": False, "mensagem": "Um dos produtos não foi encontrado."}, 400

            if not mercadoria.ativo:
                return {"sucesso": False, "mensagem": f"{mercadoria.nome} não está disponível."}, 400

            if mercadoria.quantidade < quantidade:
                return {
                    "sucesso": False,
                    "mensagem": f"Estoque insuficiente para {mercadoria.nome}."
                }, 400

            preco = mercadoria.preco_venda
            subtotal = preco * quantidade

            itens_validados.append({
                "mercadoria": mercadoria,
                "quantidade": quantidade,
                "preco": preco,
                "subtotal": subtotal,
            })

            total += subtotal

        # Pedido público: não há usuário autenticado.
        venda = Venda(
            usuario_id=current_user.id if current_user.is_authenticated else None,
            total=total,
            tipo_pedido="mesa",
            mesa=str(mesa).strip(),
            status="recebido",
        )

        db.session.add(venda)
        db.session.flush()

        for item_validado in itens_validados:
            mercadoria = item_validado["mercadoria"]
            quantidade = item_validado["quantidade"]

            item = ItemVenda(
                venda_id=venda.id,
                mercadoria_id=mercadoria.id,
                quantidade=quantidade,
                preco_unitario=item_validado["preco"],
                subtotal=item_validado["subtotal"],
            )

            db.session.add(item)
            mercadoria.quantidade -= quantidade

        db.session.commit()

        return {
            "sucesso": True,
            "mensagem": f"Pedido #{venda.id} recebido pelo GestãoBar!",
            "pedido_id": venda.id,
        }, 200

    except Exception:
        db.session.rollback()
        app.logger.exception("Erro ao registrar pedido público")
        return {
            "sucesso": False,
            "mensagem": "Não foi possível registrar o pedido. Tente novamente."
        }, 500



@app.route("/pedidos")
@login_required
def pedidos():
    vendas = Venda.query.filter_by(
        tipo_pedido="mesa"
    ).order_by(
        Venda.id.desc()
    ).all()

    return render_template(
        "pedidos.html",
        vendas=vendas
    )


@app.route("/delivery/pedidos")
@login_required
def pedidos_delivery():
    vendas = Venda.query.filter_by(
        tipo_pedido="delivery"
    ).order_by(
        Venda.id.desc()
    ).all()

    return render_template(
        "pedidos_delivery.html",
        vendas=vendas
    )


@app.route("/pedido/<int:venda_id>/preparo", methods=["POST"])
@login_required
def pedido_preparo(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "mesa":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "recebido":
        return "O pedido não está aguardando preparo.", 400

    venda.status = "em_preparo"
    db.session.commit()

    return redirect(url_for("pedidos"))


@app.route("/pedido/<int:venda_id>/pronto", methods=["POST"])
@login_required
def pedido_pronto(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "mesa":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "em_preparo":
        return "O pedido não está em preparo.", 400

    venda.status = "pronto"
    db.session.commit()

    return redirect(url_for("pedidos"))


@app.route("/pedido/<int:venda_id>/entregue", methods=["POST"])
@login_required
def pedido_entregue(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "mesa":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "pronto":
        return "O pedido não está pronto para ser entregue.", 400

    venda.status = "entregue"
    db.session.commit()

    return redirect(url_for("pedidos"))


@app.route(
    "/delivery/pedido/<int:venda_id>/preparo",
    methods=["POST"]
)
@login_required
def delivery_pedido_preparo(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "delivery":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "recebido":
        return "O pedido não está aguardando preparo.", 400

    venda.status = "em_preparo"
    db.session.commit()

    return redirect(url_for("pedidos_delivery"))


@app.route(
    "/delivery/pedido/<int:venda_id>/pronto",
    methods=["POST"]
)
@login_required
def delivery_pedido_pronto(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "delivery":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "em_preparo":
        return "O pedido não está em preparo.", 400

    venda.status = "pronto"
    db.session.commit()

    return redirect(url_for("pedidos_delivery"))


@app.route(
    "/delivery/pedido/<int:venda_id>/saiu-entrega",
    methods=["POST"]
)
@login_required
def delivery_saiu_entrega(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "delivery":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "pronto":
        return "O pedido precisa estar pronto antes de sair para entrega.", 400

    venda.status = "saiu_para_entrega"
    db.session.commit()

    return redirect(url_for("pedidos_delivery"))


@app.route(
    "/delivery/pedido/<int:venda_id>/entregue",
    methods=["POST"]
)
@login_required
def delivery_pedido_entregue(venda_id):
    venda = Venda.query.get_or_404(venda_id)

    if venda.tipo_pedido != "delivery":
        return "Tipo de pedido inválido para esta operação.", 400

    if venda.status != "saiu_para_entrega":
        return "O pedido precisa sair para entrega antes de ser concluído.", 400

    venda.status = "entregue"
    db.session.commit()

    return redirect(url_for("pedidos_delivery"))


@app.route("/delivery")
def delivery():
    produtos = Mercadoria.query.filter_by(
        ativo=True
    ).order_by(
        Mercadoria.categoria,
        Mercadoria.nome
    ).all()

    return render_template(
        "delivery.html",
        produtos=produtos
    )

@app.route("/delivery/cardapio")
def delivery_cardapio():

    categoria = request.args.get("categoria")

    if categoria:
        produtos = Mercadoria.query.filter_by(
            ativo=True,
            categoria=categoria
        ).order_by(
            Mercadoria.nome
        ).all()
    else:
        produtos = Mercadoria.query.filter_by(
            ativo=True
        ).order_by(
            Mercadoria.categoria,
            Mercadoria.nome
        ).all()

    # Preço exclusivo do Delivery
    for produto in produtos:
        if produto.categoria == "Sucos":
            produto.preco_delivery = produto.preco_venda + 2
        else:
            produto.preco_delivery = produto.preco_venda

    return render_template(
        "delivery_cardapio.html",
        produtos=produtos,
        categoria=categoria
    )


@app.route("/delivery/carrinho")
def delivery_carrinho():
    return render_template("delivery_carrinho.html")


@app.route("/delivery/finalizar", methods=["GET", "POST"])
def delivery_finalizar():
    if request.method == "GET":
        return render_template("delivery_finalizar.html")

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return {"sucesso": False, "mensagem": "Dados inválidos."}, 400

    itens = dados.get("itens")

    if not isinstance(itens, list) or not itens:
        return {"sucesso": False, "mensagem": "O carrinho está vazio."}, 400

    # Validar os dados do cliente.
    campos = [
        "cliente_nome",
        "cliente_telefone",
        "cliente_endereco",
        "cliente_numero",
        "cliente_bairro",
        "forma_pagamento",
    ]

    cliente = {
        campo: str(dados.get(campo) or "").strip()
        for campo in campos
    }

    if any(not cliente[campo] for campo in campos):
        return {
            "sucesso": False,
            "mensagem": "Preencha todos os campos obrigatórios."
        }, 400

    if cliente["forma_pagamento"] not in {
        "Pix",
        "Dinheiro",
        "Cartão de crédito",
        "Cartão de débito",
    }:
        return {
            "sucesso": False,
            "mensagem": "Forma de pagamento inválida."
        }, 400

    if any(len(valor) > limite for valor, limite in [
        (cliente["cliente_nome"], 150),
        (cliente["cliente_telefone"], 20),
        (cliente["cliente_endereco"], 200),
        (cliente["cliente_numero"], 20),
        (cliente["cliente_bairro"], 100),
    ]):
        return {
            "sucesso": False,
            "mensagem": "Um dos dados informados é muito longo."
        }, 400

    # Somar quantidades repetidas do mesmo produto.
    quantidades = {}

    try:
        for item in itens:
            if not isinstance(item, dict):
                return {
                    "sucesso": False,
                    "mensagem": "Item inválido no carrinho."
                }, 400

            produto_id = int(item.get("id"))
            quantidade = int(item.get("quantidade"))

            if produto_id <= 0 or quantidade <= 0:
                raise ValueError

            quantidades[produto_id] = (
                quantidades.get(produto_id, 0) + quantidade
            )

        if any(qtd > 100 for qtd in quantidades.values()):
            return {
                "sucesso": False,
                "mensagem": "Quantidade máxima por produto excedida."
            }, 400

    except (TypeError, ValueError):
        return {
            "sucesso": False,
            "mensagem": "Produto ou quantidade inválidos."
        }, 400

    try:
        itens_validados = []
        total_produtos = 0

        # Validar produtos e recalcular os preços pelo banco.
        for produto_id, quantidade in quantidades.items():
            mercadoria = db.session.get(Mercadoria, produto_id)

            if mercadoria is None or not mercadoria.ativo:
                db.session.rollback()
                return {
                    "sucesso": False,
                    "mensagem": "Um produto não está disponível."
                }, 400

            if mercadoria.quantidade < quantidade:
                db.session.rollback()
                return {
                    "sucesso": False,
                    "mensagem": f"Estoque insuficiente para {mercadoria.nome}."
                }, 400

            preco = float(mercadoria.preco_venda or 0)

            if preco < 0:
                db.session.rollback()
                return {
                    "sucesso": False,
                    "mensagem": "Preço de produto inválido."
                }, 400

            # Acréscimo de R$ 2,00 por unidade de suco.
            if mercadoria.categoria == "Sucos":
                preco += 2.00

            subtotal = round(preco * quantidade, 2)

            itens_validados.append({
                "mercadoria": mercadoria,
                "quantidade": quantidade,
                "preco": preco,
                "subtotal": subtotal,
            })

            total_produtos += subtotal


        # Calcular o frete usando a tabela do servidor.
        bairro_normalizado = normalizar_bairro(
            cliente["cliente_bairro"]
        )

        taxa_entrega = FRETES_POR_BAIRRO.get(bairro_normalizado)

        if taxa_entrega is None:
            db.session.rollback()
            return {
                "sucesso": False,
                "mensagem": (
                    "Não atendemos esse bairro ou ele ainda não "
                    "está cadastrado. Entre em contato com o estabelecimento."
                )
            }, 400

        total = round(total_produtos + taxa_entrega, 2)


        venda = Venda(
            usuario_id=None,
            total=total,
            taxa_entrega=taxa_entrega,
            forma_pagamento=cliente["forma_pagamento"],
            tipo_pedido="delivery",
            status="recebido",
            cliente_nome=cliente["cliente_nome"],
            cliente_telefone=cliente["cliente_telefone"],
            cliente_endereco=cliente["cliente_endereco"],
            cliente_numero=cliente["cliente_numero"],
            cliente_complemento=(
                str(dados.get("cliente_complemento") or "").strip() or None
            ),
            cliente_bairro=cliente["cliente_bairro"],
            cliente_cep=(
                str(dados.get("cliente_cep") or "").strip() or None
            ),
        )

        db.session.add(venda)
        db.session.flush()



        for item in itens_validados:
            mercadoria = item["mercadoria"]
            quantidade = item["quantidade"]

            # Descontar estoque somente se houver quantidade suficiente.
            resultado = db.session.execute(
                update(Mercadoria)
                .where(
                    Mercadoria.id == mercadoria.id,
                    Mercadoria.ativo.is_(True),
                    Mercadoria.quantidade >= quantidade
                )
                .values(
                    quantidade=Mercadoria.quantidade - quantidade
                )
            )

            if resultado.rowcount != 1:
                db.session.rollback()
                return {
                    "sucesso": False,
                    "mensagem": (
                        f"Estoque insuficiente ou produto indisponível: "
                        f"{mercadoria.nome}."
                    )
                }, 409

            # Registrar cada item dentro do laço.
            db.session.add(ItemVenda(
                venda_id=venda.id,
                mercadoria_id=mercadoria.id,
                quantidade=quantidade,
                preco_unitario=item["preco"],
                subtotal=item["subtotal"],
            ))

        # Salvar venda, itens e descontos juntos.
        db.session.commit()


        return {
            "sucesso": True,
            "mensagem": f"Pedido #{venda.id} recebido!",
            "pedido_id": venda.id,
            "total": total,
        }, 200

    except Exception:
        db.session.rollback()
        app.logger.exception("Erro ao registrar pedido de delivery")
        return {
            "sucesso": False,
            "mensagem": "Não foi possível registrar o pedido. Tente novamente."
        }, 500



@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))
