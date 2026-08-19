function atualizarData() {
    const agora = new Date();

    const data = agora.toLocaleDateString("pt-BR");

    const dia = agora.toLocaleDateString("pt-BR", {
        weekday: "long"
    });

    const dataElemento = document.getElementById("current-date");
    const diaElemento = document.getElementById("current-day");

    if (dataElemento) {
        dataElemento.textContent = data;
    }

    if (diaElemento) {
        diaElemento.textContent =
            dia.charAt(0).toUpperCase() + dia.slice(1);
}

atualizarData();