"""Cardápio do Will Japanese Restaurant.

Fonte única dos pratos e preços: o chatbot usa para responder "quanto custa o X"
e confirmar pedidos, e o site usa para montar a seção de cardápio.
"""
import re
import unicodedata

CARDAPIO = [
    {
        'categoria': 'Sushis',
        'detalhe': '8 peças',
        'itens': [
            {'nome': 'Sushi de Salmão', 'descricao': 'Salmão fresco sobre arroz temperado', 'preco': 18,
             'apelidos': ['sushi de salmão', 'sushi salmão', 'salmão', 'salmon', 'sake']},
            {'nome': 'Sushi de Atum', 'descricao': 'Atum vermelho em corte tradicional', 'preco': 20,
             'apelidos': ['sushi de atum', 'sushi atum', 'atum', 'tuna', 'maguro']},
            {'nome': 'Sushi de Kani', 'descricao': 'Kani, pepino e gergelim', 'preco': 15,
             'apelidos': ['sushi de kani', 'sushi kani', 'kani', 'caranguejo', 'surimi']},
            {'nome': 'Philadelphia', 'descricao': 'Salmão com cream cheese', 'preco': 25,
             'apelidos': ['philadelphia', 'filadélfia', 'cream cheese philadelphia']},
            {'nome': 'Hot Roll', 'descricao': '8 peças empanadas de salmão e cream cheese', 'preco': 30,
             'apelidos': ['hot roll', 'hot rolls', 'hot']},
        ],
    },
    {
        'categoria': 'Temakis',
        'detalhe': 'cone de alga',
        'itens': [
            {'nome': 'Temaki Salmão Grelhado', 'descricao': 'Salmão grelhado, cebolinha e tarê', 'preco': 22,
             'apelidos': ['temaki salmão grelhado', 'salmão grelhado', 'grilled salmon', 'temaki salmão',
                          'temaki de salmão']},
            {'nome': 'Temaki Hot Philadelphia', 'descricao': 'Empanado, salmão e cream cheese', 'preco': 28,
             'apelidos': ['temaki hot philadelphia', 'hot philadelphia']},
            {'nome': 'Temaki Califórnia', 'descricao': 'Kani, manga e pepino', 'preco': 24,
             'apelidos': ['temaki califórnia', 'califórnia', 'california roll', 'california']},
            {'nome': 'Temaki Atum Spicy', 'descricao': 'Atum picado com molho apimentado', 'preco': 26,
             'apelidos': ['temaki atum spicy', 'atum spicy', 'spicy tuna', 'spicy', 'temaki atum']},
        ],
    },
    {
        'categoria': 'Pratos quentes',
        'detalhe': 'serve 1 pessoa',
        'itens': [
            {'nome': 'Yakissoba', 'descricao': 'Macarrão salteado no wok com legumes', 'preco': 35,
             'apelidos': ['yakissoba', 'yakisoba', 'yaki soba', 'macarrão japonês']},
            {'nome': 'Udon', 'descricao': 'Macarrão grosso em caldo dashi', 'preco': 32,
             'apelidos': ['udon', 'macarrão udon', 'sopa udon']},
            {'nome': 'Teriyaki Chicken', 'descricao': 'Frango grelhado no molho teriyaki', 'preco': 38,
             'apelidos': ['teriyaki chicken', 'frango teriyaki', 'chicken teriyaki', 'teriyaki']},
        ],
    },
    {
        'categoria': 'Combinados',
        'detalhe': 'para dividir',
        'itens': [
            {'nome': 'Combo Salmão', 'descricao': '20 peças só de salmão', 'preco': 65,
             'apelidos': ['combo salmão', 'combo salmon']},
            {'nome': 'Combo Misto', 'descricao': '30 peças variadas', 'preco': 85,
             'apelidos': ['combo misto', 'combo mix', 'combo variado']},
            {'nome': 'Combo Família', 'descricao': '50 peças, serve até 4 pessoas', 'preco': 120,
             'apelidos': ['combo família', 'combo family']},
        ],
    },
]

# Palavra genérica -> categoria ("quanto custa o temaki?" responde a faixa de preço)
CATEGORIAS = {
    'sushi': 'Sushis', 'sushis': 'Sushis',
    'temaki': 'Temakis', 'temakis': 'Temakis',
    'combo': 'Combinados', 'combinado': 'Combinados', 'combinados': 'Combinados',
    'prato quente': 'Pratos quentes', 'pratos quentes': 'Pratos quentes',
}


SINGULAR = {'temakis': 'temaki', 'sushis': 'sushi', 'combos': 'combo', 'rolls': 'roll', 'combinados': 'combinado'}


def _norm(texto):
    sem_acento = ''.join(c for c in unicodedata.normalize('NFKD', texto.lower()) if not unicodedata.combining(c))
    palavras = re.sub(r'[^\w\s]', ' ', sem_acento).split()
    return ' '.join(SINGULAR.get(p, p) for p in palavras)


# Apelidos do mais longo para o mais curto: "temaki salmão grelhado" antes de "salmão"
_APELIDOS = sorted(
    ((_norm(a), item) for cat in CARDAPIO for item in cat['itens'] for a in item['apelidos']),
    key=lambda par: len(par[0]), reverse=True,
)


def reais(valor):
    return f'R$ {valor:.2f}'.replace('.', ',')


def buscar_itens(texto):
    """Pratos do cardápio citados no texto, na ordem em que aparecem."""
    alvo = f' {_norm(texto)} '
    achados = []
    for apelido, item in _APELIDOS:
        for termo in (f' {apelido}s ', f' {apelido} '):
            pos = alvo.find(termo)
            if pos >= 0:
                if item not in [i for _, i in achados]:
                    achados.append((pos, item))
                # tira o trecho para "salmão" não casar de novo dentro de "combo salmão"
                alvo = alvo[:pos] + ' ' + '#' * (len(termo) - 2) + ' ' + alvo[pos + len(termo):]
                break
    return [item for _, item in sorted(achados, key=lambda par: par[0])]


def buscar_item(texto):
    """Primeiro prato do cardápio citado no texto (ou None)."""
    itens = buscar_itens(texto)
    return itens[0] if itens else None


def buscar_categoria(texto):
    alvo = f' {_norm(texto)} '
    for palavra, categoria in sorted(CATEGORIAS.items(), key=lambda p: len(p[0]), reverse=True):
        if f' {palavra} ' in alvo:
            return next(c for c in CARDAPIO if c['categoria'] == categoria)
    return None


def remover_pratos(texto):
    """Tira do texto os nomes de pratos e categorias.

    O prato é tratado à parte (buscar_item); sem ele, a intenção é decidida pelo resto
    da frase: "quanto custa o hot roll" vira "quanto custa o", que é claramente preço.
    """
    alvo = f' {_norm(texto)} '
    termos = [a for a, _ in _APELIDOS] + sorted(CATEGORIAS, key=len, reverse=True)
    for termo in termos:
        alvo = alvo.replace(f' {termo}s ', ' ').replace(f' {termo} ', ' ')
    return alvo.strip()
