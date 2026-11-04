"""Leitura dos arquivos brutos da base Google Local e recorte de gastronomia."""

import json
import re
from collections import Counter

import numpy as np
import pandas as pd

# Termos com \b exigem a palavra inteira, para que "Barber shop" não entre por "bar".
PADRAO_ALIMENTACAO = re.compile(
    r"restaurant|caf[eé]|coffee|espresso|pizz|bakery|diner|grill|steak|burger|sandwich"
    r"|\bdeli\b|bistro|brew|ice cream|donut|doughnut|taco|burrito|sushi|buffet|bbq|barbecue"
    r"|breakfast|brunch|dessert|bagel|\bbar\b|\bpub\b|gastropub|tavern|lounge|eatery|snack"
    r"|juice|tea house|bubble tea|frozen yogurt|creamery|winery|cupcake|chocolate (?:shop|cafe)"
    r"|\bwings\b|chicken|noodle|ramen|\bpho\b|crepe|smokehouse|chophouse|hoagie|cheesesteak"
    r"|bun shop|\bfood\b"
)

CATEGORIAS_EXCLUIDAS = {
    "caterer",
    "catering food and drink supplier",
    "health food store",
    "organic food store",
    "food store",
    "wholesale food store",
    "food bank",
    "food producer",
    "food products supplier",
    "food service",
    "restaurant supply store",
    "bar stool supplier",
    "grill store",
    "bbq area",
    "coffee machine supplier",
    "coffee vending machine",
    "coffee wholesaler",
    "wholesale bakery",
    "chocolate factory",
    "tea store",
    "internet cafe",
    "bed & breakfast",
    "travel lounge",
    "hookah bar",
}

# Locais de comida ou bebida cuja categoria principal é atípica (ver 01_dados.ipynb, seção 1.2).
LOCAIS_INCLUIDOS_MANUALMENTE = {
    "0x53530fe0a5cee957:0x9b21da61d1587dc1": "Bar J Chuckwagon Suppers",
    "0x53530ff45de63d85:0x703fb07171293aeb": "Bar J Chuckwagon",
    "0x534c1f494d178205:0x469d090501205e58": "The Cody Cattle Company",
    "0x876f252b854a147f:0x334ed16cf7ca29ac": "The Outlaw Saloon",
    "0x8760bca406e2e1ed:0xf96d5cc2fb48c5d4": "Yellowstone Garage",
    "0x534c1f2a056a5ba5:0x8fe9cd6261e2e7eb": "Sunset House Restaurant",
    "0x876f3a512a550401:0x364578937dcde1a0": "Pretzelmaker (Cheyenne)",
    "0x8760bbf0545b4789:0xaf102114681fefdc": "Pretzelmaker (Casper)",
}


# Classificação dos grupos de `MISC`: o que um local recém-cadastrado poderia declarar e o que não.
GRUPOS_DECLARAVEIS = ["Service options", "Accessibility", "Amenities", "Payments", "Planning", "From the business"]
GRUPOS_DERIVADOS = ["Popular for", "Highlights", "Crowd", "Atmosphere", "Offerings", "Dining options"]
GRUPOS_TEMPORARIOS = ["Health & safety", "Health and safety"]


def _lista_categorias(categorias):
    """Devolve as categorias como lista; valor ausente vira lista vazia."""
    if isinstance(categorias, (list, tuple, np.ndarray)):
        return [categoria for categoria in categorias if isinstance(categoria, str)]
    return []


def eh_categoria_alimentacao(categoria):
    """Indica se a categoria é de local de consumo de comida ou bebida."""
    categoria = categoria.strip().lower()
    return categoria not in CATEGORIAS_EXCLUIDAS and bool(PADRAO_ALIMENTACAO.search(categoria))


def categoria_principal(categorias):
    """Primeira categoria da lista que não seja `Caterer`; sem nenhuma, devolve None."""
    for categoria in _lista_categorias(categorias):
        if categoria.strip().lower() != "caterer":
            return categoria
    return None


def tem_categoria_alimentacao(categorias):
    """Indica se alguma categoria da lista, principal ou não, é de alimentação."""
    return any(eh_categoria_alimentacao(categoria) for categoria in _lista_categorias(categorias))


def eh_gastronomia(categorias):
    """Indica se a categoria principal do local é de alimentação."""
    principal = categoria_principal(categorias)
    return principal is not None and eh_categoria_alimentacao(principal)


def no_recorte(locais):
    """Marca os locais do recorte: categoria principal de alimentação ou inclusão manual."""
    return locais["category"].map(eh_gastronomia) | locais["gmap_id"].isin(LOCAIS_INCLUIDOS_MANUALMENTE)


def contar_avaliacoes_por_local(caminho):
    """Conta, linha a linha, as avaliações de cada `gmap_id` no arquivo bruto."""
    with open(caminho, encoding="utf-8") as arquivo:
        return Counter(json.loads(linha)["gmap_id"] for linha in arquivo)


def ler_metadados(caminho):
    """Lê todos os campos dos locais, sem nenhum tratamento."""
    with open(caminho, encoding="utf-8") as arquivo:
        return pd.DataFrame([json.loads(linha) for linha in arquivo])


def ler_avaliacoes(caminho, gmap_ids):
    """Lê, linha a linha, só as avaliações dos locais em `gmap_ids` (equivale a um inner join).

    `pics` e `resp` viram os indicadores `tem_foto` e `tem_resposta`.
    """
    gmap_ids = set(gmap_ids)
    colunas = {
        nome: []
        for nome in ["user_id", "gmap_id", "rating", "time", "text", "tem_foto", "tem_resposta"]
    }
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            avaliacao = json.loads(linha)
            if avaliacao["gmap_id"] not in gmap_ids:
                continue
            colunas["user_id"].append(avaliacao["user_id"])
            colunas["gmap_id"].append(avaliacao["gmap_id"])
            colunas["rating"].append(avaliacao["rating"])
            colunas["time"].append(avaliacao["time"])
            colunas["text"].append(avaliacao["text"])
            colunas["tem_foto"].append(bool(avaliacao["pics"]))
            colunas["tem_resposta"].append(bool(avaliacao["resp"]))
    return pd.DataFrame(colunas).astype(
        {"rating": "float64", "time": "int64", "tem_foto": "bool", "tem_resposta": "bool"}
    )


def copias_identicas(locais):
    """Indica se todas as linhas com `gmap_id` repetido são cópias idênticas."""
    repetidos = locais[locais["gmap_id"].duplicated(keep=False)]
    if repetidos.empty:
        return True
    textos = repetidos.apply(lambda linha: json.dumps(linha.to_dict(), sort_keys=True, default=str), axis=1)
    return bool(textos.groupby(repetidos["gmap_id"]).nunique().eq(1).all())


def extrair_cidade_cep(endereco):
    """Extrai a cidade e o CEP do final do endereço (`..., Cidade, WY 82520`)."""
    if not isinstance(endereco, str):
        return None, None
    cidade = re.search(r"([^,]+),\s*WY\s+\d{5}", endereco)
    cep = re.search(r"\b(?:WY|Wyoming)\s+(\d{5})", endereco)
    return (cidade.group(1).strip() if cidade else None, cep.group(1) if cep else None)


def nivel_de_preco(preco):
    """Conta os símbolos `$` ou `₩` (artefato da coleta); valor ausente vira NaN."""
    if not isinstance(preco, str):
        return np.nan
    return float(sum(simbolo in "$₩" for simbolo in preco))


def limpar_locais(locais):
    """Trata os metadados dos locais selecionados, sem olhar as avaliações."""
    if not copias_identicas(locais):
        raise ValueError("Há gmap_id repetido com conteúdo diferente.")
    limpos = locais.drop_duplicates("gmap_id").reset_index(drop=True)
    limpos = limpos.drop(columns=["url", "hours"]).rename(
        columns={"avg_rating": "avg_rating_google", "num_of_reviews": "num_of_reviews_google"}
    )
    limpos["categoria_principal"] = limpos["category"].map(categoria_principal)
    cidades_ceps = limpos["address"].map(extrair_cidade_cep)
    limpos["cidade"] = cidades_ceps.str[0]
    limpos["cep"] = cidades_ceps.str[1]
    fora_de_wyoming = ~(limpos["latitude"].between(40.5, 45.5) & limpos["longitude"].between(-111.6, -103.5))
    limpos.loc[fora_de_wyoming, ["latitude", "longitude"]] = np.nan
    limpos["preco_nivel"] = limpos["price"].map(nivel_de_preco)
    estado = limpos["state"].map(lambda valor: valor if isinstance(valor, str) else "")
    limpos["fechado_perm"] = estado.str.startswith("Permanently closed")
    limpos["fechado_temp"] = estado.str.startswith("Temporarily closed")
    return limpos


def limpar_avaliacoes(avaliacoes):
    """Trata as avaliações e devolve a tabela limpa e o funil de linhas removidas."""
    funil = [("Avaliações do recorte", len(avaliacoes), 0)]

    def registrar(etapa, tabela, anterior):
        funil.append((etapa, len(tabela), anterior - len(tabela)))
        return tabela

    limpas = registrar(
        "Sem nota ou sem usuário", avaliacoes.dropna(subset=["rating", "user_id"]), len(avaliacoes)
    )
    limpas = registrar(
        "Duplicatas exatas",
        limpas.drop_duplicates(["user_id", "gmap_id", "time", "rating", "text"]),
        len(limpas),
    )
    limpas = registrar(
        "Mesmo usuário e local, fica a mais recente",
        limpas.sort_values("time", kind="stable").drop_duplicates(["user_id", "gmap_id"], keep="last").sort_index(),
        len(limpas),
    )
    if not limpas["rating"].isin([1, 2, 3, 4, 5]).all():
        raise ValueError("Há nota fora dos inteiros de 1 a 5.")

    limpas = limpas.reset_index(drop=True).astype({"rating": "int64"})
    limpas["data"] = pd.to_datetime(limpas["time"], unit="ms")
    limpas["ano"] = limpas["data"].dt.year
    limpas["mes"] = limpas["data"].dt.month
    limpas["tem_texto"] = limpas["text"].notna()
    limpas = limpas.drop(columns="time")
    return limpas, pd.DataFrame(funil, columns=["etapa", "linhas", "removidas"])


def indice_gini(valores):
    """Índice de Gini: 0 é distribuição igual; perto de 1, tudo concentrado em poucos."""
    ordenados = np.sort(np.asarray(valores, dtype=float))
    n = len(ordenados)
    return float((2 * np.arange(1, n + 1) - n - 1) @ ordenados / (n * ordenados.sum()))


def atributos_do_local(misc):
    """Lista os atributos de `MISC` no formato `grupo: valor`."""
    if not isinstance(misc, dict):
        return []
    return [
        f"{grupo}: {valor}"
        for grupo, valores in misc.items()
        if isinstance(valores, (list, tuple, np.ndarray))
        for valor in valores
    ]


def marcar_rajadas(avaliacoes, minimo=5):
    """Marca as avaliações de usuários com ao menos `minimo` avaliações no mesmo minuto."""
    chaves = [avaliacoes["user_id"], avaliacoes["data"].dt.floor("min")]
    return avaliacoes.groupby(chaves)["gmap_id"].transform("size") >= minimo
