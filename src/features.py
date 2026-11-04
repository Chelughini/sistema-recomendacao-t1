"""Representação de conteúdo dos locais: tokens e vetorização TF-IDF por bloco."""

import re

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.dados import GRUPOS_DECLARAVEIS, GRUPOS_DERIVADOS

# Dependem do comportamento dos clientes ou surgiram na pandemia (ver 02_preparacao.ipynb, seção 2.1).
VALORES_EXCLUIDOS = {"Usually a wait", "Quick visit", "Curbside pickup", "No-contact delivery"}

# Grafias diferentes da mesma ideia.
SINONIMOS = {
    "Wheelchair-accessible car park": "Wheelchair accessible parking lot",
    "Wheelchair-accessible entrance": "Wheelchair accessible entrance",
    "Wheelchair-accessible lift": "Wheelchair accessible elevator",
    "Wheelchair-accessible seating": "Wheelchair accessible seating",
    "Wheelchair-accessible toilet": "Wheelchair accessible restroom",
    "Bar on site": "Bar onsite",
    "Gender-neutral toilets": "Gender-neutral restroom",
    "Toilets": "Restroom",
    "Cash-only": "Cash only",
    "Cheques": "Checks",
    "Takeaway": "Takeout",
}

BLOCOS = ("categorias", "atributos")


def _normalizar(texto):
    return re.sub(r"\s+", "_", texto.strip().lower())


def _lista(valores):
    if isinstance(valores, (list, tuple, np.ndarray)):
        return [valor for valor in valores if isinstance(valor, str)]
    return []


def tokens_do_local(local, incluir_derivados=False, incluir_preco=False):
    """Gera os tokens de um local, vindo de uma linha da tabela ou de um cadastro manual.

    O cadastro manual é um dicionário com `category` (lista) e `MISC` (grupo -> lista de valores).
    As opções `incluir_*` servem só para medir o quanto se abre mão ao deixar esses dados fora.
    """
    categorias = [f"cat={_normalizar(categoria)}" for categoria in _lista(local.get("category"))]
    atributos = []
    misc = local.get("MISC")
    if isinstance(misc, dict):
        grupos = GRUPOS_DECLARAVEIS + (GRUPOS_DERIVADOS if incluir_derivados else [])
        for grupo in grupos:
            for valor in _lista(misc.get(grupo)):
                if valor not in VALORES_EXCLUIDOS:
                    atributos.append(f"misc={_normalizar(grupo)}:{_normalizar(SINONIMOS.get(valor, valor))}")
    nivel = local.get("preco_nivel")
    if incluir_preco and isinstance(nivel, (int, float)) and not np.isnan(nivel):
        atributos.append(f"misc=preco:{int(nivel)}")
    return {"categorias": list(dict.fromkeys(categorias)), "atributos": list(dict.fromkeys(atributos))}


def _tokens_prontos(tokens):
    """Analisador do TF-IDF: os documentos já são listas de tokens."""
    return tokens


def _documentos_por_bloco(locais, **opcoes):
    registros = locais.to_dict("records") if hasattr(locais, "to_dict") else locais
    tokens = [tokens_do_local(local, **opcoes) for local in registros]
    return {bloco: [local[bloco] for local in tokens] for bloco in BLOCOS}


class VetorizadorConteudo:
    """TF-IDF por bloco, ponderação por bloco e normalização L2 final (produto escalar = cosseno).

    Ajuste só com os locais do treino correspondente. Tokens desconhecidos são ignorados, o que
    permite vetorizar um local novo. Peso 0 remove o bloco.
    """

    def __init__(self, peso_categorias=1.0, peso_atributos=1.0, incluir_derivados=False, incluir_preco=False):
        self.pesos = {"categorias": peso_categorias, "atributos": peso_atributos}
        self.opcoes = {"incluir_derivados": incluir_derivados, "incluir_preco": incluir_preco}
        if min(self.pesos.values()) < 0 or max(self.pesos.values()) == 0:
            raise ValueError("Os pesos não podem ser negativos, e ao menos um deve ser positivo.")

    def fit(self, locais):
        documentos = _documentos_por_bloco(locais, **self.opcoes)
        self.vetorizadores_ = {
            bloco: TfidfVectorizer(analyzer=_tokens_prontos, sublinear_tf=True, norm="l2", min_df=2).fit(documentos[bloco])
            for bloco in BLOCOS
            if self.pesos[bloco] > 0
        }
        return self

    def transform(self, locais):
        documentos = _documentos_por_bloco(locais, **self.opcoes)
        partes = [
            vetorizador.transform(documentos[bloco]) * self.pesos[bloco]
            for bloco, vetorizador in self.vetorizadores_.items()
        ]
        return normalize(sparse.hstack(partes, format="csr"), norm="l2")

    def fit_transform(self, locais):
        return self.fit(locais).transform(locais)

    def nomes_features(self):
        """Nomes das colunas da matriz, na mesma ordem, usados nas explicações."""
        return np.concatenate(
            [vetorizador.get_feature_names_out() for vetorizador in self.vetorizadores_.values()]
        )

    def idf_por_token(self):
        """IDF de cada token, na ordem das colunas da matriz."""
        valores = np.concatenate([vetorizador.idf_ for vetorizador in self.vetorizadores_.values()])
        return pd.Series(valores, index=self.nomes_features(), name="idf")
