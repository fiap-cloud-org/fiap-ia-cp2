import logging
import os

from flask import Flask, jsonify, render_template, request

from chatbot import chatbot
from menu import CARDAPIO, reais

app = Flask(__name__)
log = logging.getLogger(__name__)
app.add_template_filter(reais, 'reais')


@app.route('/')
def home():
    return render_template(
        'home.html',
        cardapio=CARDAPIO,
        total_pratos=sum(len(c['itens']) for c in CARDAPIO),
        total_intencoes=len(chatbot.intents['intents']),
    )


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get('message', '')).strip()
    if not message:
        return jsonify({'error': 'Mensagem não fornecida'}), 400
    if len(message) > 500:
        return jsonify({'error': 'Mensagem muito longa (máximo de 500 caracteres)'}), 400

    try:
        result = chatbot.get_response(message)
    except Exception:
        log.exception('Erro ao processar a mensagem')
        return jsonify({'error': 'Erro interno ao processar a mensagem'}), 500

    return jsonify({
        'response': result['response'],
        'intent': result['intent'],
        'probability': result['probability'],
        'all_intents': result.get('all_intents', []),
        'all_probabilities': result.get('all_probabilities', []),
        'sentences_processed': result.get('sentences_processed', 1),
        'multiple_sentences': result.get('sentences_processed', 1) > 1,
    })


@app.route('/intents')
def get_intents():
    """Lista as intenções carregadas."""
    return jsonify(chatbot.intents)


if __name__ == '__main__':
    # Modo debug só quando pedido explicitamente (FLASK_DEBUG=1)
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(debug=debug, host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', '5000')))
