'use strict';

// Widget de atendimento: envia a mensagem para POST /chat e mostra a resposta
// com as intenções detectadas e a confiança de cada uma.
(function chat() {
    const raiz = document.getElementById('chat');
    const painel = document.getElementById('chatPainel');
    const botao = document.getElementById('chatBotao');
    const fechar = document.getElementById('chatFechar');
    const mensagens = document.getElementById('chatMensagens');
    const form = document.getElementById('chatForm');
    const entrada = document.getElementById('chatEntrada');
    const enviar = document.getElementById('chatEnviar');
    const sugestoes = document.getElementById('chatSugestoes');
    if (!raiz || !painel || !form) return;

    const NOMES = {
        cumprimento: 'cumprimento', compra: 'pedido', itens_disponiveis: 'cardápio', precos: 'preço',
        tempo_entrega: 'entrega', agradecimento: 'agradecimento', reclamacao: 'reclamação', despedida: 'despedida',
        localizacao: 'endereço', horario_funcionamento: 'horário', ingredientes_qualidade: 'ingredientes',
        promocoes_ofertas: 'promoções', informacoes_nutricionais: 'nutrição', curiosidades_cultura: 'cultura',
        forma_pagamento: 'pagamento', eventos_grupos: 'eventos', desconhecido: 'não entendi',
    };
    let ocupado = false;

    function abrir(aberto) {
        raiz.classList.toggle('aberto', aberto);
        painel.setAttribute('aria-hidden', String(!aberto));
        botao.setAttribute('aria-expanded', String(aberto));
        botao.setAttribute('aria-label', aberto ? 'Fechar atendimento' : 'Abrir atendimento');
        if (aberto) setTimeout(() => entrada.focus({ preventScroll: true }), 180);
    }

    botao.addEventListener('click', () => abrir(!raiz.classList.contains('aberto')));
    fechar.addEventListener('click', () => abrir(false));
    document.querySelectorAll('[data-abrir-chat]').forEach((b) => b.addEventListener('click', () => abrir(true)));
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && raiz.classList.contains('aberto')) abrir(false);
    });

    // Clicar num prato do cardápio abre o chat e já faz o pedido
    document.querySelectorAll('[data-pedir]').forEach((b) => b.addEventListener('click', () => {
        abrir(true);
        enviarMensagem(b.dataset.pedir);
    }));

    function escapar(texto) {
        return texto.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    function formatar(texto) {
        return escapar(texto.trim()).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
    }

    function rolar() {
        mensagens.scrollTop = mensagens.scrollHeight;
    }

    function adicionar(texto, de, intencoes) {
        const el = document.createElement('div');
        el.className = `msg ${de}`;
        el.innerHTML = `<div class="balao">${formatar(texto)}</div>`;
        if (intencoes && intencoes.length) {
            const tags = intencoes.map(([nome, p]) => `<span><b>${escapar(NOMES[nome] || nome)}</b>${Math.round(p)}%</span>`).join('');
            el.insertAdjacentHTML('beforeend', `<div class="intencoes" title="Intenção detectada e confiança">${tags}</div>`);
        }
        mensagens.appendChild(el);
        rolar();
    }

    function digitando() {
        const el = document.createElement('div');
        el.className = 'msg bot digitando';
        el.setAttribute('aria-label', 'Digitando');
        el.innerHTML = '<div class="balao"><i></i><i></i><i></i></div>';
        mensagens.appendChild(el);
        rolar();
        return el;
    }

    async function enviarMensagem(texto) {
        if (!texto || ocupado) return;
        ocupado = true;
        enviar.disabled = true;
        adicionar(texto, 'user');
        entrada.value = '';
        const indicador = digitando();
        // Pausa curta só para o "digitando" ser percebido; a resposta chega em milissegundos
        const pausa = new Promise((r) => setTimeout(r, 350));

        try {
            const resp = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: texto }),
            });
            const dados = await resp.json();
            await pausa;
            indicador.remove();
            if (!resp.ok) throw new Error(dados.error || 'erro');
            const nomes = dados.all_intents && dados.all_intents.length ? dados.all_intents : [dados.intent];
            const probs = dados.all_probabilities && dados.all_probabilities.length ? dados.all_probabilities : [dados.probability];
            adicionar(dados.response, 'bot', nomes.map((n, i) => [n, probs[i] ?? 0]));
        } catch (err) {
            await pausa;
            indicador.remove();
            adicionar('Sumimasen! Não consegui responder agora. Tente de novo em instantes.', 'bot');
        } finally {
            ocupado = false;
            enviar.disabled = false;
            entrada.focus({ preventScroll: true });
        }
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        enviarMensagem(entrada.value.trim());
    });

    sugestoes.addEventListener('click', (e) => {
        const b = e.target.closest('button');
        if (b) enviarMensagem(b.textContent.trim());
    });
})();
