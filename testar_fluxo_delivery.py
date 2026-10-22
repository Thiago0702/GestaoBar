
def avancar_status(tipo_pedido, status_atual, proximo_status):
    """Valida a transição sem acessar o banco de dados."""

    transicoes = {
        "recebido": ("em_preparo", "O pedido não está aguardando preparo."),
        "em_preparo": ("pronto", "O pedido não está em preparo."),
        "pronto": (
            "saiu_para_entrega",
            "O pedido precisa estar pronto antes de sair para entrega.",
        ),
        "saiu_para_entrega": (
            "entregue",
            "O pedido precisa sair para entrega antes de ser concluído.",
        ),
    }

    if tipo_pedido != "delivery":
        return False, "Tipo de pedido inválido para esta operação."

    transicao = transicoes.get(status_atual)

    if transicao is None:
        return False, "Status atual inválido para esta operação."

    status_esperado, mensagem_erro = transicao

    if proximo_status != status_esperado:
        return False, mensagem_erro

    return True, proximo_status


def testar_fluxo_delivery():
    status = "recebido"

    etapas = [
        ("em_preparo", "em_preparo"),
        ("pronto", "pronto"),
        ("saiu_para_entrega", "saiu_para_entrega"),
        ("entregue", "entregue"),
    ]

    for proximo_status, esperado in etapas:
        sucesso, resultado = avancar_status(
            "delivery", status, proximo_status
        )

        assert sucesso, f"Falha ao avançar de {status}: {resultado}"
        assert resultado == esperado
        status = resultado
        print(f"OK: status atualizado para {status}")

    # Um pedido de mesa não pode usar a transição de delivery.
    sucesso, _ = avancar_status("mesa", "recebido", "em_preparo")
    assert not sucesso, "A validação deveria rejeitar pedido de mesa."

    # Não deve permitir pular diretamente de recebido para pronto.
    sucesso, _ = avancar_status("delivery", "recebido", "pronto")
    assert not sucesso, "A validação deveria impedir pular etapas."

    print("OK: pedido de mesa rejeitado.")
    print("OK: pulo de etapas rejeitado.")
    print("Todos os testes passaram.")


if __name__ == "__main__":
    testar_fluxo_delivery()
