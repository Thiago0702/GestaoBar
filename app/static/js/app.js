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
}


function abrirCalendario() {
    const calendario = document.getElementById("calendario");

    if (calendario) {
        calendario.showPicker();
    }
}


function selecionarData() {
    const calendario = document.getElementById("calendario");

    if (!calendario || !calendario.value) {
        return;
    }

    window.location.href = "/?data=" + calendario.value;
}

// ========================================
// CENTRAL DE NOTIFICAÇÕES - GESTÃOBAR
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    const botao = document.getElementById("botao-notificacoes");
    const painel = document.getElementById("painel-notificacoes");
    const contador = document.getElementById("contador-notificacoes");
    const lista = document.getElementById("lista-notificacoes");

    if (!botao || !painel || !contador || !lista) {
        return;
    }

    let pedidosConhecidos = null;
    let audioContext = null;

    // Abre e fecha o painel
    botao.addEventListener("click", function () {
        const aberto = painel.style.display !== "none";
        painel.style.display = aberto ? "none" : "block";

        // Prepara o áudio após interação do usuário
        if (!audioContext) {
            const AudioContext =
                window.AudioContext || window.webkitAudioContext;

            if (AudioContext) {
                audioContext = new AudioContext();
            }
        }

        if (audioContext && audioContext.state === "suspended") {
            audioContext.resume();
        }
    });

    // Som de notificação
    function tocarSom() {
        if (!audioContext || audioContext.state !== "running") {
            return;
        }

        const oscilador = audioContext.createOscillator();
        const volume = audioContext.createGain();

        oscilador.connect(volume);
        volume.connect(audioContext.destination);

        oscilador.frequency.value = 880;
        volume.gain.setValueAtTime(0.15, audioContext.currentTime);
        volume.gain.exponentialRampToValueAtTime(
            0.001,
            audioContext.currentTime + 0.4
        );

        oscilador.start();
        oscilador.stop(audioContext.currentTime + 0.4);
    }

    // Consulta os pedidos novos
    async function atualizarNotificacoes() {
        try {
            const resposta = await fetch("/api/pedidos/novos");

            if (!resposta.ok) {
                throw new Error("Não foi possível consultar os pedidos.");
            }

            const dados = await resposta.json();
            const pedidos = dados.pedidos || [];

            contador.textContent = dados.total || 0;
            contador.style.display = dados.total > 0 ? "inline-flex" : "none";

            // Na primeira consulta, apenas registra os pedidos existentes.
            const idsAtuais = pedidos.map(pedido =>
                `${pedido.tipo}-${pedido.id}`
            );

            if (pedidosConhecidos !== null) {
                const novosPedidos = idsAtuais.filter(id =>
                    !pedidosConhecidos.includes(id)
                );

                if (novosPedidos.length > 0) {
                    tocarSom();
                }
            }

            pedidosConhecidos = idsAtuais;

            // Atualiza a lista do painel
            lista.innerHTML = "";

            if (pedidos.length === 0) {
                lista.innerHTML = "<p>Nenhum pedido novo.</p>";
                return;
            }

            pedidos.forEach(pedido => {
                const item = document.createElement("a");

                item.className = "notificacao-item";

                if (pedido.tipo === "delivery") {
                    item.href = "/delivery/pedidos";
                    item.textContent = `🚚 Pedido Delivery #${pedido.id}`;
                } else {
                    item.href = "/pedidos";
                    item.textContent = `🍽️ Pedido de Mesa #${pedido.id}`;
                }

                lista.appendChild(item);
            });

        } catch (erro) {
            console.error("Erro nas notificações:", erro);
        }
    }

    atualizarNotificacoes();

    // Atualiza a cada 10 segundos
    setInterval(atualizarNotificacoes, 10000);

});