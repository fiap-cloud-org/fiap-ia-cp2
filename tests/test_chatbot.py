"""Testes do chatbot: cada frase precisa cair na intenção certa."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import chatbot  # noqa: E402

FRASES = [
    # As 8 intenções obrigatórias
    ("Olá", "cumprimento"),
    ("Boa noite!", "cumprimento"),
    ("Oi, tudo bem?", "cumprimento"),
    ("Quero pedir sushi de salmão", "compra"),
    ("Quero hot roll", "compra"),
    ("Preciso de yakissoba", "compra"),
    ("Gostaria de philadelphia", "compra"),
    ("Vou querer califórnia", "compra"),
    ("Quero fazer um pedido", "compra"),
    ("Qual o cardápio?", "itens_disponiveis"),
    ("Quais pratos vocês têm?", "itens_disponiveis"),
    ("O que tem no menu?", "itens_disponiveis"),
    ("Quanto custa o temaki?", "precos"),
    ("Qual o preço do combo família?", "precos"),
    ("Qual o valor do yakissoba?", "precos"),
    ("Qual o tempo de entrega?", "tempo_entrega"),
    ("Quanto tempo demora?", "tempo_entrega"),
    ("Em quanto tempo chega?", "tempo_entrega"),
    ("Muito obrigado", "agradecimento"),
    ("Valeu pela ajuda", "agradecimento"),
    ("Arigato!", "agradecimento"),
    ("Meu pedido chegou frio", "reclamacao"),
    ("O sushi veio mal feito", "reclamacao"),
    ("Demorou muito para entregar", "reclamacao"),
    ("Tchau", "despedida"),
    ("Até logo", "despedida"),
    ("Sayonara", "despedida"),
    # Intenções extras
    ("Onde fica o restaurante?", "localizacao"),
    ("Qual o endereço de vocês?", "localizacao"),
    ("Que horas vocês fecham?", "horario_funcionamento"),
    ("Vocês abrem no domingo?", "horario_funcionamento"),
    ("Quais as formas de pagamento?", "forma_pagamento"),
    ("Vocês aceitam pix?", "forma_pagamento"),
    ("Posso pagar no cartão de crédito?", "forma_pagamento"),
    ("Tem alguma promoção?", "promocoes_ofertas"),
    ("Tem cupom de desconto?", "promocoes_ofertas"),
    ("O salmão é fresco?", "ingredientes_qualidade"),
    ("Quantas calorias tem um temaki?", "informacoes_nutricionais"),
    ("Tem opção sem lactose?", "informacoes_nutricionais"),
    ("Vocês fazem festa de aniversário?", "eventos_grupos"),
    ("Qual a história do sushi?", "curiosidades_cultura"),
]


@pytest.mark.parametrize("frase,esperada", FRASES)
def test_intencao(frase, esperada):
    r = chatbot.get_response(frase)
    assert r["intent"] == esperada, f"{frase!r}: {r['all_intents']} {r['all_probabilities']}"


def test_frase_sem_sentido_nao_tem_intencao():
    r = chatbot.get_response("asdfgh qwerty zxcv")
    assert r["intent"] == "desconhecido"
    assert "não entendi" in r["response"].lower()


def test_varias_frases_na_mesma_mensagem():
    r = chatbot.get_response("Boa noite, quero sushi de atum e também gostaria de saber o tempo de entrega.")
    assert r["all_intents"] == ["cumprimento", "compra", "tempo_entrega"]
    assert r["sentences_processed"] == 3


def test_virgula_separa_cumprimento_da_pergunta():
    r = chatbot.get_response("Oi, quanto custa o temaki?")
    assert r["all_intents"] == ["cumprimento", "precos"]


def test_pedido_com_prato_confirma_o_prato():
    r = chatbot.get_response("Quero um hot roll")
    assert r["intent"] == "compra"
    assert "hot roll" in r["response"].lower()


def test_probabilidades_entre_0_e_100():
    r = chatbot.get_response("Olá! Qual o horário de funcionamento? Aceita pix?")
    assert len(r["all_probabilities"]) == 3
    assert all(0 <= p <= 100 for p in r["all_probabilities"])
