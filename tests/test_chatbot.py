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
    assert "Pedido anotado: Hot Roll (R$ 30,00)" in r["response"]


def test_probabilidades_entre_0_e_100():
    r = chatbot.get_response("Olá! Qual o horário de funcionamento? Aceita pix?")
    assert len(r["all_probabilities"]) == 3
    assert all(0 <= p <= 100 for p in r["all_probabilities"])


def test_cumprimento_uma_vez_por_mensagem():
    for _ in range(20):
        r = chatbot.get_response("Olá! Boa noite!")
        assert r["all_intents"] == ["cumprimento", "cumprimento"]
        assert "\n\n" not in r["response"]


def test_preco_do_prato_citado():
    r = chatbot.get_response("Quanto custa o sushi de atum e o hot roll?")
    assert r["intent"] == "precos"
    assert "Sushi de Atum custa R$ 20,00" in r["response"]
    assert "Hot Roll custa R$ 30,00" in r["response"]


def test_preco_da_categoria():
    r = chatbot.get_response("Quanto custa o temaki?")
    assert "de R$ 22,00 a R$ 28,00" in r["response"]


def test_preco_usa_o_prato_citado_antes_na_mensagem():
    r = chatbot.get_response("Quero um combo salmão, quanto custa?")
    assert r["all_intents"] == ["compra", "precos"]
    assert "Combo Salmão custa R$ 65,00" in r["response"]


def test_pedido_com_dois_pratos():
    r = chatbot.get_response("Quero um hot roll e um temaki califórnia")
    assert "Pedido anotado: Hot Roll (R$ 30,00) e Temaki Califórnia (R$ 24,00)" in r["response"]


def test_pedido_de_categoria_pergunta_qual():
    r = chatbot.get_response("Quero pedir um temaki")
    assert r["intent"] == "compra"
    assert "Qual você prefere?" in r["response"]
