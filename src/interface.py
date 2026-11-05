"""Funções da interface (`app.py`) que não dependem do Streamlit."""

from html import escape

import numpy as np
import pandas as pd

from src.dados import GRUPOS_DECLARAVEIS
from src.features import SINONIMOS, VALORES_EXCLUIDOS, _normalizar
from src.graficos import numero_br
from src.recomendador import pontuar as pontuar_componentes
from src.traducoes import traduzir_token

NIVEIS_DE_PRECO = {1: "$ (barato)", 2: "$$ (moderado)", 3: "$$$ (caro)", 4: "$$$$ (muito caro)"}


def _lista(valores):
    if isinstance(valores, (list, tuple, np.ndarray)):
        return [valor for valor in valores if isinstance(valor, str)]
    return []


def rotulo_categoria(categoria):
    """Categoria em português; sem tradução, o nome original."""
    return traduzir_token(f"cat={_normalizar(categoria)}") or categoria


def rotulo_categorias(categorias, quantidade=3):
    rotulos = list(dict.fromkeys(rotulo_categoria(categoria) for categoria in _lista(categorias)))
    return ", ".join(rotulos[:quantidade])


class NumeracaoUsuarios:
    """Mostra cada usuário como "Usuário #N", sem o identificador do Google.

    A numeração segue a ordem alfabética dos identificadores, então não muda entre execuções.
    """

    def __init__(self, usuarios):
        self.ids = np.sort(np.asarray(usuarios).astype(str))
        self._numero = pd.Series(np.arange(1, len(self.ids) + 1), index=self.ids)

    def __len__(self):
        return len(self.ids)

    def numero(self, usuario):
        return int(self._numero[usuario]) if usuario in self._numero.index else None

    def rotulo(self, usuario):
        return f"Usuário #{numero_br(self.numero(usuario))}"

    def buscar(self, texto):
        """Aceita o número (com ou sem "#" e ponto de milhar) ou o identificador; sem resultado, None."""
        texto = (texto or "").strip()
        if not texto:
            return None
        if texto in self._numero.index:
            return texto
        numero = texto.lstrip("#").replace(".", "").strip()
        if numero.isdigit() and 1 <= int(numero) <= len(self.ids):
            return self.ids[int(numero) - 1]
        return None


def _vocabulario(modelo):
    return set(modelo.nomes_tokens)


def opcoes_categorias(modelo):
    """Rótulo em português -> categoria original, só das categorias que o modelo conhece."""
    vocabulario = _vocabulario(modelo)
    contagem = pd.Series([categoria for valor in modelo.locais["category"] for categoria in _lista(valor)]).value_counts()
    opcoes = {}
    for categoria in contagem.index:
        if f"cat={_normalizar(categoria)}" in vocabulario:
            opcoes.setdefault(rotulo_categoria(categoria), categoria)
    return dict(sorted(opcoes.items()))


def opcoes_atributos(modelo):
    """Rótulo em português -> (grupo, valor), só dos atributos declaráveis que o modelo conhece."""
    vocabulario = _vocabulario(modelo)
    opcoes = {}
    for misc in modelo.locais["MISC"]:
        if not isinstance(misc, dict):
            continue
        for grupo in GRUPOS_DECLARAVEIS:
            for valor in _lista(misc.get(grupo)):
                if valor in VALORES_EXCLUIDOS:
                    continue
                token = f"misc={_normalizar(grupo)}:{_normalizar(SINONIMOS.get(valor, valor))}"
                rotulo = traduzir_token(token)
                if token in vocabulario and rotulo is not None:
                    opcoes.setdefault(rotulo, (grupo, valor))
    return dict(sorted(opcoes.items()))


def atributos_declarados(pares):
    """Lista de (grupo, valor) -> dicionário grupo -> valores, no formato de `MISC`; vazio vira None."""
    misc = {}
    for grupo, valor in pares:
        misc.setdefault(grupo, []).append(valor)
    return misc or None


def resumo_do_perfil(modelo, usuario, quantidade=5):
    """Tokens com maior peso positivo (gosta mais) e negativo (gosta menos) no perfil, traduzidos."""
    perfil = np.asarray(modelo.perfis[modelo._linha_perfil[usuario]].todense()).ravel()
    resumo = {}
    for chave, ordem in [("gosta", np.argsort(-perfil, kind="stable")), ("evita", np.argsort(perfil, kind="stable"))]:
        sinal = 1 if chave == "gosta" else -1
        tokens = []
        for indice in ordem:
            if sinal * perfil[indice] <= 0 or len(tokens) == quantidade:
                break
            traducao = traduzir_token(modelo.nomes_tokens[indice])
            if traducao is not None:
                tokens.append(traducao)
        resumo[chave] = tokens
    return resumo


def historico_do_usuario(modelo, usuario):
    """Locais que o usuário avaliou no treino, das notas maiores para as menores."""
    avaliacoes = modelo.treino[modelo.treino["user_id"] == usuario]
    dados = modelo.locais.set_index("gmap_id").loc[avaliacoes["gmap_id"]]
    tabela = pd.DataFrame(
        {
            "Local": dados["name"].to_numpy(),
            "Cidade": dados["cidade"].fillna("sem cidade").to_numpy(),
            "Categorias": [rotulo_categorias(valor) for valor in dados["category"]],
            "Nota": avaliacoes["rating"].astype(int).to_numpy(),
        }
    )
    return tabela.sort_values(["Nota", "Local"], ascending=[False, True], kind="stable").reset_index(drop=True)


def cidades_do_usuario(modelo, usuario):
    """Quantas avaliações o usuário tem em cada cidade, da mais frequente para a menos."""
    return historico_do_usuario(modelo, usuario)["Cidade"].value_counts()


def motivo_para_local_novo(modelo, usuario, vetor_local, cidade=None):
    """Frase curta com o porquê de indicar um local novo a um usuário: onde ele avalia e o que tem em comum."""
    cidades = cidades_do_usuario(modelo, usuario)
    total = int(cidades.sum())
    if isinstance(cidade, str) and cidades.get(cidade, 0) > 0:
        frase = f"Avaliou {cidades[cidade]} de {total} locais em {cidade}."
    elif (cidades.index != "sem cidade").any():
        principal = cidades[cidades.index != "sem cidade"]
        frase = f"Avalia sobretudo em {principal.index[0]} ({principal.iloc[0]} de {total})."
    else:
        frase = f"Tem {total} avaliações em locais sem cidade."
    tokens = modelo._tokens_que_mais_pesam(modelo.perfis_local_novo[modelo._linha_perfil[usuario]], vetor_local)
    if tokens:
        frase += f" Em comum com o perfil: {', '.join(tokens)}."
    return frase


def cadastro_do_local(local):
    """Linha da tabela de locais -> cadastro no formato aceito pelo recomendador."""
    return {
        "name": local["name"],
        "category": _lista(local["category"]),
        "MISC": local["MISC"] if isinstance(local["MISC"], dict) else {},
        "cidade": local["cidade"] if isinstance(local["cidade"], str) else None,
        "latitude": local["latitude"],
        "longitude": local["longitude"],
    }


# ------------------------------------------------------------------ Demonstração

# Família visual de cada categoria principal: ícone e cor do cartão, pela primeira palavra-chave que casar.
# As cores são tons do tema da apresentação (terracota, mostarda, sálvia e marrons).
FAMILIAS = [
    (("coffee", "cafe", "espresso", "tea"), "☕", "#6B4226"),
    (("pizza",), "🍕", "#B44E1C"),
    (("mexican", "taco", "burrito", "latin", "tex-mex"), "🌮", "#CC8B20"),
    (("hamburger", "fast food", "hot dog"), "🍔", "#A06A12"),
    (("chinese", "asian", "japanese", "sushi", "thai", "vietnamese", "korean", "indian"), "🥢", "#8A3A14"),
    (("bakery", "donut", "dessert", "ice cream", "cake", "cupcake", "cookie", "chocolate", "frozen yogurt"), "🍩", "#C9765A"),
    (("steak", "barbecue", "grill", "chophouse"), "🥩", "#5C260C"),
    (("sandwich", "deli", "bagel", "sub"), "🥪", "#697967"),
    (("breakfast", "brunch", "diner", "family", "pancake"), "🍳", "#8A9A87"),
    (("bar", "brew", "pub", "beer", "wine", "cocktail", "tavern", "lounge", "saloon", "distillery"), "🍺", "#4E5A4C"),
]
FAMILIA_PADRAO = ("🍽️", "#333F48")


def familia(categoria):
    """Ícone e cor de uma categoria principal; sem palavra-chave conhecida, o garfo e faca."""
    texto = categoria.lower() if isinstance(categoria, str) else ""
    for chaves, icone, cor in FAMILIAS:
        if any(chave in texto for chave in chaves):
            return icone, cor
    return FAMILIA_PADRAO


def pesos_do_perfil(modelo, usuario, gosta=6, evita=4):
    """Tokens traduzidos com os maiores pesos positivos e negativos do perfil, para o gráfico."""
    perfil = np.asarray(modelo.perfis[modelo._linha_perfil[usuario]].todense()).ravel()
    linhas = []
    for ordem, quantidade, sinal in [(np.argsort(-perfil, kind="stable"), gosta, 1), (np.argsort(perfil, kind="stable"), evita, -1)]:
        tomados = 0
        for indice in ordem:
            if sinal * perfil[indice] <= 0 or tomados == quantidade:
                break
            traducao = traduzir_token(modelo.nomes_tokens[indice])
            if traducao is not None:
                linhas.append({"caracteristica": traducao, "peso": float(perfil[indice]), "sentido": "gosta mais" if sinal > 0 else "gosta menos"})
                tomados += 1
    return pd.DataFrame(linhas, columns=["caracteristica", "peso", "sentido"])


def prateleiras(modelo, usuario, n=10, profundidade=40, minimo=3):
    """Linhas de recomendações no estilo de catálogo, todas tiradas da pontuação do modelo.

    - "Top para você": a lista do cenário 1, com a cota de locais novos;
    - "Porque você gostou de X": os locais da lista ampliada cuja explicação aponta X (até 2 linhas);
    - "Novidades para você": os locais sem avaliações, pela mesma pontuação;
    - "Bem avaliados perto de você": a lista ampliada reordenada pelo escore, entre os próximos.
    """
    ampla = modelo.recomendar(usuario, n=profundidade, com_explicacao=False)
    explicacoes = [modelo.explicar(usuario, gmap_id) for gmap_id in ampla["gmap_id"]]
    ampla["explicacao"] = [explicacao["frase"] for explicacao in explicacoes]
    ampla["parecido"] = [explicacao["parecido"]["nome"] if explicacao["parecido"] else None for explicacao in explicacoes]
    # O top sai de uma chamada própria: na lista ampliada, a cota vale para as `profundidade` posições, não para as n.
    linhas = [{"titulo": "Top para você", "tabela": modelo.recomendar(usuario, n=n)}]

    for nome, quantidade in ampla["parecido"].value_counts().head(2).items():
        if quantidade >= minimo:
            linhas.append({"titulo": f"Porque você gostou de {nome}", "tabela": ampla[ampla["parecido"] == nome].head(n)})

    if len(modelo.locais_novos):
        componentes = modelo.componentes([usuario], modelo.locais_novos)
        pontuacoes = pontuar_componentes(componentes, modelo.pesos)[0]
        ordem = np.argsort(-pontuacoes, kind="stable")[:n]
        por_candidato = {chave: (valor[0] if np.ndim(valor) == 2 else valor) for chave, valor in componentes.items()}
        novos = modelo._tabela_de_lista(np.asarray(modelo.locais_novos), ordem, pontuacoes, por_candidato)
        novos["novo"] = True
        novos["explicacao"] = [modelo.explicar(usuario, gmap_id)["frase"] for gmap_id in novos["gmap_id"]]
        linhas.append({"titulo": "Novidades para você", "tabela": novos})

    perto = ampla[ampla["local"] >= ampla["local"].median()].sort_values("escore", ascending=False, kind="stable")
    linhas.append({"titulo": "Bem avaliados perto de você", "tabela": perto.head(n)})
    return linhas


ESTILO_PRATELEIRA = """
<style>
.prateleira {display:flex; gap:12px; overflow-x:auto; padding:4px 2px 14px; scroll-snap-type:x mandatory;}
.prateleira::-webkit-scrollbar {height:8px;}
.prateleira::-webkit-scrollbar-thumb {background:rgba(128,128,128,.35); border-radius:4px;}
.cartao {flex:0 0 190px; scroll-snap-align:start; border-radius:10px; overflow:hidden;
  background:rgba(128,128,128,.08); border:1px solid rgba(128,128,128,.22); transition:transform .15s;}
.cartao:hover {transform:scale(1.04);}
.capa {height:96px; display:flex; align-items:center; justify-content:center; font-size:44px; position:relative;}
.selo {position:absolute; top:8px; left:8px; background:#333F48; color:#fff; font-size:11px; font-weight:700;
  padding:2px 7px; border-radius:4px; letter-spacing:.04em;}
.posicao {position:absolute; bottom:4px; right:10px; color:rgba(255,255,255,.85); font-size:26px; font-weight:800;}
.corpo {padding:8px 10px 10px; font-size:12.5px; line-height:1.35;}
.nome {font-weight:700; font-size:14px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:38px;}
.cidade {opacity:.75;}
.categorias {opacity:.75; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.match {color:#B44E1C; font-weight:700; margin-top:4px;}
.porque {opacity:.7; font-size:11.5px; margin-top:4px; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;}
</style>
"""


def cartao_html(linha, posicao, categorias, nota_prevista=None):
    """Um cartão: capa com o ícone da categoria, nome, cidade, compatibilidade e o porquê."""
    icone, cor = familia(linha["categoria_principal"])
    selo = '<span class="selo">NOVO</span>' if bool(linha.get("novo", False)) else ""
    cidade = linha["cidade"] if isinstance(linha["cidade"], str) else "sem cidade"
    nota = f" · ★ {numero_br(nota_prevista, 1)}" if nota_prevista is not None else ""
    porque = linha.get("explicacao")
    porque_html = f'<div class="porque">{escape(porque)}</div>' if isinstance(porque, str) else ""
    return (
        f'<div class="cartao"><div class="capa" style="background:linear-gradient(135deg,{cor},{cor}99)">{selo}{icone}'
        f'<span class="posicao">{posicao}</span></div><div class="corpo">'
        f'<div class="nome">{escape(str(linha["nome"]))}</div><div class="cidade">{escape(cidade)}</div>'
        f'<div class="categorias">{escape(categorias)}</div>'
        f'<div class="match">{numero_br(100 * linha["pontuacao"])}% compatível{nota}</div>{porque_html}</div></div>'
    )
