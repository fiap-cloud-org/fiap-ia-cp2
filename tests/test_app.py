"""Testes das rotas Flask."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402

cliente = app.test_client()


def test_home_mostra_o_cardapio():
    r = cliente.get('/')
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'Will Japanese Restaurant' in html
    assert 'R$ 30,00' in html  # Hot Roll
    assert 'data-pedir="Quero um Hot Roll"' in html


def test_chat_responde_com_intencao_e_confianca():
    r = cliente.post('/chat', json={'message': 'Qual o tempo de entrega?'})
    assert r.status_code == 200
    dados = r.get_json()
    assert dados['intent'] == 'tempo_entrega'
    assert 0 < dados['probability'] <= 100
    assert dados['response']


def test_chat_com_varias_frases():
    r = cliente.post('/chat', json={'message': 'Olá! Aceita pix?'})
    dados = r.get_json()
    assert dados['all_intents'] == ['cumprimento', 'forma_pagamento']
    assert dados['multiple_sentences'] is True


def test_chat_sem_mensagem_devolve_400():
    assert cliente.post('/chat', json={}).status_code == 400
    assert cliente.post('/chat', data='nada', content_type='text/plain').status_code == 400


def test_chat_mensagem_longa_devolve_400():
    assert cliente.post('/chat', json={'message': 'a' * 501}).status_code == 400


def test_intents_lista_as_16_intencoes():
    dados = cliente.get('/intents').get_json()
    assert len(dados['intents']) == 16
