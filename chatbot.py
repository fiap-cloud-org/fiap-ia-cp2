import json
import random
import re
import nltk
from collections import Counter
import math
from pathlib import Path

# Recursos do NLTK: baixados na primeira execução (o punkt_tab é exigido a partir do NLTK 3.9)
for recurso, caminho in [('punkt_tab', 'tokenizers/punkt_tab'), ('stopwords', 'corpora/stopwords')]:
    try:
        nltk.data.find(caminho)
    except LookupError:
        nltk.download(recurso, quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class RestauranteJaponesChatbotSimples:
    def __init__(self):
        self.intents = self.load_intents()
        self.stop_words = set(stopwords.words('portuguese'))
        # Adiciona algumas palavras em inglês também
        self.stop_words.update(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])

    def extract_prato(self, text):
        """Extrai o prato japonês da frase, considerando variações e erros comuns."""
        pratos = [
            # Sushis tradicionais (ordem por especificidade)
            "philadelphia", "filadélfia", "cream cheese philadelphia",
            "sushi de salmão", "sushi salmão", "salmão", "salmao", "salmon", "sake",
            "sushi de atum", "sushi atum", "atum", "tuna", "maguro",
            "sushi de kani", "sushi kani", "kani", "caranguejo", "surimi",
            
            # Temakis especiais
            "temaki hot philadelphia", "hot philadelphia", "hot roll",
            "temaki salmão grelhado", "salmão grelhado", "salmao grelhado", "grilled salmon",
            "temaki califórnia", "temaki california", "califórnia", "california", "california roll",
            "temaki atum spicy", "atum spicy", "spicy tuna", "spicy",
            "temaki salmão", "temaki salmao", 
            "temaki atum", "temaki kani", "temaki",
            
            # Pratos quentes
            "yakissoba de frango", "yakissoba frango", "yakissoba carne", "yakissoba misto",
            "yakissoba", "yakisoba", "yaki soba", "macarrão japonês",
            "udon de frango", "udon carne", "udon vegetariano", "udon",
            "macarrão udon", "sopa udon",
            "teriyaki chicken", "frango teriyaki", "chicken teriyaki", "teriyaki",
            "ramen", "lamen", "missoshiru", "miso soup", "sopa de miso",
            "gyoza", "guioza", "tempura", "tempora",
            
            # Combinados e especiais
            "combo família", "combo familia", "combo family",
            "combo salmão", "combo salmao", "combo salmon",
            "combo misto", "combo mix", "combo variado",
            "combo atum", "combo tuna",
            "combo executivo", "combo especial", "combo premium",
            "combinado", "combo", "rodízio", "festival",
            
            # Sashimi
            "sashimi de salmão", "sashimi salmão", "sashimi salmao",
            "sashimi de atum", "sashimi atum", "sashimi tuna",
            "sashimi misto", "sashimi mix", "sashimi",
            
            # Gunkan e outros
            "gunkan salmão", "gunkan atum", "gunkan ikura", "gunkan",
            "joe salmão", "joe atum", "joe",
            "skin salmão", "skin salmon", "skin",
            
            # Opções especiais
            "vegetariano", "vegano", "vegan", "sem peixe", "sem carne",
            "sem glúten", "diet", "light", "fitness"
        ]
        
        text_lower = text.lower()
        pratos_encontrados = []
        
        # Busca por pratos, priorizando os mais específicos
        for prato in pratos:
            if prato in text_lower:
                pratos_encontrados.append(prato)
        
        # Retorna o prato mais específico (mais longo)
        if pratos_encontrados:
            pratos_encontrados.sort(key=len, reverse=True)
            return pratos_encontrados[0]
        
        return None

    def load_intents(self):
        """Carrega as intenções do arquivo intents.json"""
        caminho = Path(__file__).with_name('intents.json')
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def preprocess_text(self, text):
        """Pré-processa o texto removendo pontuação e palavras irrelevantes"""
        # Remove pontuação e converte para minúsculo
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Tokeniza
        words = word_tokenize(text, language='portuguese')
        # Remove stop words
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        return words
    
    def calculate_similarity(self, text1_words, text2_words):
        """Calcula similaridade entre duas listas de palavras usando Jaccard"""
        if not text1_words or not text2_words:
            return 0.0
        
        set1 = set(text1_words)
        set2 = set(text2_words)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def predict_intent(self, message):
        """Prediz a intenção da mensagem usando similaridade de palavras"""
        message_words = self.preprocess_text(message)
        
        best_intent = "desconhecido"
        best_score = 0.0
        
        for intent in self.intents['intents']:
            max_similarity = 0.0
            
            for pattern in intent['patterns']:
                pattern_words = self.preprocess_text(pattern)
                similarity = self.calculate_similarity(message_words, pattern_words)
                
                if similarity > max_similarity:
                    max_similarity = similarity
            
            if max_similarity > best_score:
                best_score = max_similarity
                best_intent = intent['tag']
        
        # Se a similaridade for muito baixa, tenta busca por palavras-chave
        if best_score < 0.1:
            best_intent, best_score = self.keyword_fallback(message.lower())
        
        return best_intent, best_score
    
    def keyword_fallback(self, message):
        """Busca por palavras-chave específicas se a similaridade for baixa"""
        keywords = {
            'cumprimento': ['oi', 'olá', 'ola', 'hello', 'hey', 'bom dia', 'boa tarde', 'boa noite'],
            'compra': [
                'quero', 'pedir', 'comprar', 'pedido', 'vou querer',
                # Sushis
                'salmão', 'salmao', 'salmon', 'sake',
                'atum', 'tuna', 'maguro',
                'kani', 'caranguejo', 'surimi',
                'philadelphia', 'filadélfia', 'cream cheese',
                # Temakis
                'temaki', 'temaki salmão', 'temaki atum', 'temaki kani',
                'hot roll', 'hot philadelphia', 'hot', 'hott',
                'califórnia', 'california', 'california roll',
                'atum spicy', 'spicy tuna', 'spicy',
                'salmão grelhado', 'salmao grelhado', 'grilled salmon',
                # Pratos quentes
                'yakissoba', 'yakisoba', 'yaki soba', 'macarrão japonês',
                'udon', 'macarrão udon', 'sopa udon',
                'teriyaki', 'teriyaki chicken', 'frango teriyaki',
                # Combinados
                'combo', 'combinado', 'combo salmão', 'combo salmao',
                'combo misto', 'combo família', 'combo familia',
                'combo atum', 'rodízio', 'festival',
                # Frases completas
                'quero salmão', 'quero atum', 'quero temaki', 'quero yakissoba',
                'quero combo', 'quero udon', 'quero hot roll', 'quero califórnia'
            ],
            'itens_disponiveis': ['cardápio', 'menu', 'sabores', 'sushis', 'opções', 'tem', 'pratos', 'temakis', 'yakissoba', 'combinados'],
            'precos': ['preço', 'preco', 'valor', 'custa', 'quanto'],
            'tempo_entrega': ['tempo', 'entrega', 'demora', 'prazo', 'quando'],
            'agradecimento': ['obrigado', 'obrigada', 'valeu', 'brigado', 'thanks'],
            'reclamacao': ['problema', 'reclamação', 'ruim', 'fria', 'errada', 'atrasada'],
            'despedida': ['tchau', 'bye', 'até logo', 'falou', 'até mais', 'adeus']
        }
        
        best_intent = "desconhecido"
        best_score = 0.0
        
        for intent, words in keywords.items():
            score = sum(1 for word in words if word in message)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Normaliza o score
        if best_score > 0:
            best_score = min(0.8, best_score * 0.3)
        
        return best_intent, best_score
    
    def get_response(self, message):
        """Retorna resposta para a mensagem, identificando múltiplas intenções e pedidos de sabor."""
        # Normaliza a mensagem
        message = message.strip()
        
        # Divide a mensagem em frases se houver múltiplas
        # Melhora a detecção de separadores de frases
        sentences = re.split(r'[.!?;]+|\s+e\s+|\s+,\s*(?=quero|preciso|gostaria|vou)', message)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            sentences = [message]

        responses = []
        intents_detected = []
        probabilities = []
        sabor_confirmado = False

        for sentence in sentences:
            if sentence:
                intent, probability = self.predict_intent(sentence)
                intents_detected.append(intent)
                probabilities.append(probability)

                prato = self.extract_prato(sentence)
                
                # Se for pedido de compra e tem prato, responde confirmando o pedido
                if intent == "compra" and prato:
                    responses.append(f"Pedido anotado! Seu(a) {prato.title()} está sendo preparado(a) pelo nosso sushiman. Deseja adicionar algo mais? 🍣")
                    sabor_confirmado = True
                    continue

                # Se for itens disponíveis, responde normalmente
                if intent == "itens_disponiveis":
                    for intent_data in self.intents['intents']:
                        if intent_data['tag'] == intent:
                            response = random.choice(intent_data['responses'])
                            responses.append(response)
                            break
                    continue

                # Se for cumprimento, responde só uma vez por conversa
                if intent == "cumprimento" and len([r for r in responses if "bem-vindo" in r.lower() or "konnichiwa" in r.lower()]) == 0:
                    for intent_data in self.intents['intents']:
                        if intent_data['tag'] == intent:
                            response = random.choice(intent_data['responses'])
                            responses.append(response)
                            break
                    continue

                # Se for compra sem prato, responde normalmente
                if intent == "compra" and not prato:
                    for intent_data in self.intents['intents']:
                        if intent_data['tag'] == intent:
                            response = random.choice(intent_data['responses'])
                            responses.append(response)
                            break
                    continue

                # Outras intenções
                response_found = False
                for intent_data in self.intents['intents']:
                    if intent_data['tag'] == intent:
                        response = random.choice(intent_data['responses'])
                        responses.append(response)
                        response_found = True
                        break
                if not response_found:
                    responses.append("Desculpe, não entendi muito bem. Pode me falar mais sobre o que você precisa?")

        # Remove respostas muito similares
        final_responses = []
        for r in responses:
            similar_found = False
            for existing in final_responses:
                if len(set(r.split()) & set(existing.split())) > len(r.split()) * 0.6:
                    similar_found = True
                    break
            if not similar_found:
                final_responses.append(r)

        if len(final_responses) > 1:
            final_response = "\n\n".join(final_responses)
        else:
            final_response = final_responses[0] if final_responses else "Desculpe, não entendi. Pode repetir?"

        # Retorna a intenção e probabilidade mais alta
        if probabilities:
            max_prob_idx = probabilities.index(max(probabilities))
            main_intent = intents_detected[max_prob_idx]
            main_probability = probabilities[max_prob_idx]
        else:
            main_intent = "desconhecido"
            main_probability = 0.0

        return {
            'response': final_response,
            'intent': main_intent,
            'probability': round(main_probability * 100, 2),
            'all_intents': intents_detected,
            'all_probabilities': [round(p * 100, 2) for p in probabilities],
            'sentences_processed': len(sentences)
        }

# Instância global do chatbot
chatbot = RestauranteJaponesChatbotSimples()

if __name__ == "__main__":
    print("Chatbot do Will Japanese Restaurant iniciado!")
    print("Digite 'sair' para encerrar.")
    
    while True:
        user_input = input("\nVocê: ")
        if user_input.lower() == 'sair':
            break
        
        result = chatbot.get_response(user_input)
        print(f"\nBot: {result['response']}")
        print(f"Intenção detectada: {result['intent']}")
        print(f"Probabilidade: {result['probability']}%")
        if result['sentences_processed'] > 1:
            print(f"Frases processadas: {result['sentences_processed']}")
            print(f"Todas as intenções: {result['all_intents']}")
            print(f"Todas as probabilidades: {result['all_probabilities']}%")