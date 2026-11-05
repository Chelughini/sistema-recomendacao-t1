"""Referências fora da técnica escolhida: vizinhos por item e PageRank personalizado.

Servem só para mostrar o que se ganha e o que se perde mantendo a técnica de conteúdo e escores.
Nenhuma delas pontua um local sem avaliações no treino.
"""

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import normalize

REINICIO_PADRAO = 0.5


class _GrafoUsuarioLocal:
    """Matriz binária usuários × locais do treino, com os índices de cada lado."""

    def __init__(self, treino):
        pares = treino[["user_id", "gmap_id"]].drop_duplicates()
        self.usuarios = pd.Index(np.sort(pares["user_id"].unique().astype(str)))
        self.locais = pd.Index(np.sort(pares["gmap_id"].unique().astype(str)))
        self.matriz = sparse.csr_matrix(
            (
                np.ones(len(pares)),
                (self.usuarios.get_indexer(pares["user_id"].astype(str)), self.locais.get_indexer(pares["gmap_id"].astype(str))),
            ),
            shape=(len(self.usuarios), len(self.locais)),
        )

    def linhas(self, usuarios):
        posicoes = self.usuarios.get_indexer(np.asarray(usuarios).astype(str))
        if (posicoes < 0).any():
            raise ValueError("Há usuário sem avaliações no treino.")
        return self.matriz[posicoes]

    def colunas(self, candidatos):
        """Posição de cada candidato no grafo; -1 para quem não tem avaliações no treino."""
        return self.locais.get_indexer(np.asarray(candidatos).astype(str))


def _espalhar(pontuacoes_no_grafo, colunas):
    """Leva as pontuações às colunas dos candidatos; candidato fora do grafo fica NaN (não pontuável)."""
    resultado = np.full((pontuacoes_no_grafo.shape[0], len(colunas)), np.nan)
    presentes = colunas >= 0
    resultado[:, presentes] = pontuacoes_no_grafo[:, colunas[presentes]]
    return resultado


def _normalizar_por_usuario(pontuacoes):
    """Divide cada linha pelo seu máximo, para combinar com componentes em [0, 1]; a ordem não muda."""
    maximos = np.nanmax(pontuacoes, axis=1, keepdims=True)
    return np.divide(pontuacoes, maximos, out=np.zeros_like(pontuacoes), where=maximos > 0)


class VizinhosPorItem:
    """Vizinhos por item com cosseno na matriz binária (presença da avaliação, não a nota).

    A pontuação de um candidato é a média das similaridades com os locais que o usuário avaliou.
    """

    def ajustar(self, treino):
        self.grafo = _GrafoUsuarioLocal(treino)
        colunas_normalizadas = normalize(self.grafo.matriz.T.tocsr(), norm="l2")
        self.similaridades = (colunas_normalizadas @ colunas_normalizadas.T).toarray()
        np.fill_diagonal(self.similaridades, 0.0)
        return self

    def pontuar(self, usuarios, candidatos, normalizar=False):
        historicos = self.grafo.linhas(usuarios)
        totais = np.asarray(historicos.sum(axis=1))
        pontuacoes = np.asarray(historicos @ self.similaridades) / np.maximum(totais, 1)
        resultado = _espalhar(pontuacoes, self.grafo.colunas(candidatos))
        return _normalizar_por_usuario(resultado) if normalizar else resultado


class PageRankPersonalizado:
    """Passeio aleatório no grafo bipartido usuário–local, reiniciando no usuário com probabilidade `reinicio`.

    Do usuário, o passeio vai a um local que ele avaliou; do local, a um usuário que o avaliou, sempre
    com probabilidade uniforme. A parte dos locais satisfaz `q = c·x_u + (1 − c)²·q·M`, com
    `M = P(local → usuário) · P(usuário → local)` e `x_u` a linha normalizada do usuário; a pontuação
    do local é `(1 − c)·q`. A iteração converge porque `(1 − c)² < 1`.
    """

    def __init__(self, reinicio=REINICIO_PADRAO, iteracoes=40, tolerancia=1e-10):
        self.reinicio = reinicio
        self.iteracoes = iteracoes
        self.tolerancia = tolerancia

    def ajustar(self, treino):
        self.grafo = _GrafoUsuarioLocal(treino)
        usuario_para_local = normalize(self.grafo.matriz, norm="l1")
        local_para_usuario = normalize(self.grafo.matriz.T.tocsr(), norm="l1")
        self.transicao = (local_para_usuario @ usuario_para_local).toarray()
        self._usuario_para_local = usuario_para_local
        return self

    def pontuar(self, usuarios, candidatos, normalizar=False):
        posicoes = self.grafo.usuarios.get_indexer(np.asarray(usuarios).astype(str))
        if (posicoes < 0).any():
            raise ValueError("Há usuário sem avaliações no treino.")
        partida = self._usuario_para_local[posicoes].toarray()
        c = self.reinicio
        q = c * partida
        for _ in range(self.iteracoes):
            proximo = c * partida + (1 - c) ** 2 * (q @ self.transicao)
            if np.abs(proximo - q).max() < self.tolerancia:
                q = proximo
                break
            q = proximo
        resultado = _espalhar((1 - c) * q, self.grafo.colunas(candidatos))
        return _normalizar_por_usuario(resultado) if normalizar else resultado
