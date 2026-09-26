import json
import math
import random
import re
import unicodedata
from pathlib import Path

import nltk

# Recursos do NLTK: baixados na primeira execução (o punkt_tab é exigido a partir do NLTK 3.9)
for recurso, caminho in [('punkt_tab', 'tokenizers/punkt_tab'),
                         ('stopwords', 'corpora/stopwords'),
                         ('rslp', 'stemmers/rslp')]:
    try:
        nltk.data.find(caminho)
    except LookupError:
        nltk.download(recurso, quiet=True)

from nltk.corpus import stopwords  # noqa: E402
from nltk.stem import RSLPStemmer  # noqa: E402
from nltk.tokenize import word_tokenize  # noqa: E402

# Palavras que estão na lista de stopwords do NLTK mas mudam o sentido da frase:
# "qual o preço", "quanto tempo", "onde fica", "até logo", "não gostei"...
PALAVRAS_QUE_IMPORTAM = {'qual', 'quais', 'quanto', 'quanta', 'quantos', 'quantas', 'quando',
                         'como', 'onde', 'tem', 'nao', 'ate', 'mais', 'muito'}

# Início de uma nova pergunta ou pedido dentro da mesma mensagem.
# Usado para separar "Oi, quanto custa o temaki e em quanto tempo chega?" em três frases.
INICIO_DE_FRASE = (r'(?:quero|queria|preciso|gostaria|vou|qual|quais|quanto|quanta|quantos|quando|como|'
                   r'onde|em quanto|tem|t[êe]m|voc[êe]s?|aceit|pode|podem|tamb[ée]m|obrigad|valeu|tchau|at[ée] )')
SEPARADOR_DE_FRASES = re.compile(
    rf'[.!?;\n]+|,\s*(?={INICIO_DE_FRASE})|\s+e\s+(?={INICIO_DE_FRASE})', re.IGNORECASE)

VERBO_DE_PEDIDO = re.compile(r'\b(quero|queria|gostaria|vou querer|preciso|me v[êe]|manda|pedir|pe[çc]o)\b', re.IGNORECASE)


def sem_acento(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))


class RestauranteJaponesChatbotSimples:
    def __init__(self):
        self.intents = self.load_intents()
        self.stemmer = RSLPStemmer()
        stop = {sem_acento(w) for w in stopwords.words('portuguese')}
        stop.update(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        self.stop_words = stop - PALAVRAS_QUE_IMPORTAM
        self._indexar()

    def _indexar(self):
        """Pré-processa as frases de exemplo uma vez e calcula o peso (IDF) de cada radical.

        Um radical que aparece em poucas intenções (ex.: "cust" de custa, "pix") pesa mais
        do que um que aparece em quase todas (ex.: "salma" de salmão).
        """
        self.padroes = {}
        presenca = {}
        for intent in self.intents['intents']:
            conjuntos = []
            for pattern in intent['patterns']:
                palavras = frozenset(self.preprocess_text(pattern))
                if palavras:
                    conjuntos.append(palavras)
            self.padroes[intent['tag']] = conjuntos
            for radical in set().union(*conjuntos) if conjuntos else set():
                presenca[radical] = presenca.get(radical, 0) + 1
        total = len(self.padroes)
        self.idf = {r: math.log(1 + total / n) for r, n in presenca.items()}
        self.idf_desconhecida = 1.0

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
        """Minúsculas, sem acento e sem pontuação; tokeniza, tira stopwords e reduz ao radical (RSLP)."""
        text = re.sub(r'[^\w\s]', ' ', sem_acento(text.lower()))
        words = word_tokenize(text, language='portuguese')
        return [self.stemmer.stem(w) for w in words if w not in self.stop_words and len(w) > 1]

    def _peso(self, palavras):
        return sum(self.idf.get(p, self.idf_desconhecida) for p in palavras)

    def calculate_similarity(self, text1_words, text2_words):
        """Jaccard ponderado pelo IDF, combinado com a cobertura da frase de exemplo.

        A cobertura (quanto da frase de exemplo aparece na mensagem) ajuda quando o cliente
        escreve uma frase longa que contém um exemplo curto, como "vocês aceitam pix?".
        """
        if not text1_words or not text2_words:
            return 0.0
        set1, set2 = set(text1_words), set(text2_words)
        comum = self._peso(set1 & set2)
        if comum == 0:
            return 0.0
        jaccard = comum / self._peso(set1 | set2)
        cobertura = comum / self._peso(set2)
        return 0.5 * jaccard + 0.5 * cobertura * (comum / self._peso(set1))

    def predict_intent(self, message):
        """Prediz a intenção da mensagem pela frase de exemplo mais parecida."""
        message_words = self.preprocess_text(message)

        best_intent = "desconhecido"
        best_score = 0.0
        for tag, conjuntos in self.padroes.items():
            # Média das 3 frases de exemplo mais parecidas: um exemplo fora do lugar
            # sozinho não decide a intenção.
            notas = sorted((self.calculate_similarity(message_words, c) for c in conjuntos), reverse=True)[:3]
            score = sum(notas) / 3 if notas else 0.0
            if score > best_score:
                best_score = score
                best_intent = tag

        # Similaridade muito baixa: tenta as palavras-chave
        if best_score < 0.15:
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
    
    def resposta_da_intencao(self, tag):
        for intent_data in self.intents['intents']:
            if intent_data['tag'] == tag:
                return random.choice(intent_data['responses'])
        return "Desculpe, não entendi muito bem. Pode me falar mais sobre o que você precisa?"

    def get_response(self, message):
        """Retorna resposta para a mensagem, identificando múltiplas intenções e pedidos de sabor."""
        # Normaliza a mensagem
        message = message.strip()
        
        # Divide a mensagem em frases se houver múltiplas
        # Melhora a detecção de separadores de frases
        sentences = SEPARADOR_DE_FRASES.split(message)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            sentences = [message]

        responses = []
        intents_detected = []
        probabilities = []
        cumprimentou = False

        for sentence in sentences:
            if sentence:
                intent, probability = self.predict_intent(sentence)
                prato = self.extract_prato(sentence)

                # "Gostaria de philadelphia": verbo de desejo + prato é pedido, não consulta ao cardápio
                if prato and intent in ('itens_disponiveis', 'desconhecido') and VERBO_DE_PEDIDO.search(sentence):
                    intent = 'compra'
                    probability = max(probability, 0.5)

                intents_detected.append(intent)
                probabilities.append(probability)
                
                # Se for pedido de compra e tem prato, responde confirmando o pedido
                if intent == "compra" and prato:
                    responses.append(f"Pedido anotado! Seu(a) {prato.title()} está sendo preparado(a) pelo nosso sushiman. Deseja adicionar algo mais? 🍣")
                    continue

                # Se for itens disponíveis, responde normalmente
                if intent == "itens_disponiveis":
                    for intent_data in self.intents['intents']:
                        if intent_data['tag'] == intent:
                            response = random.choice(intent_data['responses'])
                            responses.append(response)
                            break
                    continue

                # Cumprimento: responde só uma vez por mensagem ("Oi, boa noite!" não vira dois olás)
                if intent == "cumprimento":
                    if not cumprimentou:
                        responses.append(self.resposta_da_intencao(intent))
                        cumprimentou = True
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