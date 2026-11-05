import numpy as np
import pandas as pd
import pytest

from src.referencias import PageRankPersonalizado, VizinhosPorItem


def _treino():
    pares = [("u1", "a"), ("u1", "b"), ("u2", "a"), ("u2", "c"), ("u3", "c"), ("u3", "d")]
    return pd.DataFrame(pares, columns=["user_id", "gmap_id"]).assign(rating=5)


def test_vizinhos_por_item_com_resultado_conhecido():
    modelo = VizinhosPorItem().ajustar(_treino())
    # Colunas binárias: a = {u1, u2}, b = {u1}, c = {u2, u3}, d = {u3}.
    # cos(a, b) = 1/√2; cos(a, c) = 1/2; cos(b, c) = 0; cos(a, d) = 0; cos(b, d) = 0.
    pontuacoes = modelo.pontuar(["u1"], ["c", "d", "a"])
    # u1 avaliou a e b: c = (1/2 + 0) / 2; d = 0; a = (0 + 1/√2) / 2, pois a diagonal é zerada.
    assert pontuacoes[0] == pytest.approx([0.25, 0.0, 1 / (2 * np.sqrt(2))])


def test_vizinhos_nao_pontuam_local_sem_avaliacoes_e_exigem_usuario_conhecido():
    modelo = VizinhosPorItem().ajustar(_treino())
    assert np.isnan(modelo.pontuar(["u1"], ["novo", "c"])[0, 0])
    with pytest.raises(ValueError):
        modelo.pontuar(["ninguem"], ["a"])


def test_normalizar_divide_pelo_maximo_do_usuario():
    pontuacoes = VizinhosPorItem().ajustar(_treino()).pontuar(["u1"], ["c", "d", "a"], normalizar=True)
    assert np.nanmax(pontuacoes) == pytest.approx(1.0)
    assert np.argsort(pontuacoes[0]).tolist() == [1, 0, 2]


def _pagerank_explicito(treino, usuario, reinicio, passos=500):
    """Passeio no grafo bipartido inteiro, por iteração de potência, para conferir a forma fechada."""
    usuarios = sorted(treino["user_id"].unique())
    locais = sorted(treino["gmap_id"].unique())
    nos = usuarios + locais
    indice = {no: i for i, no in enumerate(nos)}
    adjacencia = np.zeros((len(nos), len(nos)))
    for u, l in treino[["user_id", "gmap_id"]].itertuples(index=False):
        adjacencia[indice[u], indice[l]] = adjacencia[indice[l], indice[u]] = 1
    transicao = adjacencia / adjacencia.sum(axis=1, keepdims=True)
    partida = np.zeros(len(nos))
    partida[indice[usuario]] = 1
    r = partida.copy()
    for _ in range(passos):
        r = reinicio * partida + (1 - reinicio) * r @ transicao
    return pd.Series(r[len(usuarios) :], index=locais)


@pytest.mark.parametrize("reinicio", [0.5, 0.2])
def test_pagerank_coincide_com_o_passeio_no_grafo_inteiro(reinicio):
    treino = _treino()
    modelo = PageRankPersonalizado(reinicio=reinicio, iteracoes=500).ajustar(treino)
    esperado = _pagerank_explicito(treino, "u1", reinicio)
    assert modelo.pontuar(["u1"], list(esperado.index))[0] == pytest.approx(esperado.to_numpy(), abs=1e-9)


def test_pagerank_favorece_o_que_esta_perto_no_grafo_e_nao_pontua_local_novo():
    modelo = PageRankPersonalizado().ajustar(_treino())
    pontuacoes = modelo.pontuar(["u1"], ["c", "d", "novo"])[0]
    assert pontuacoes[0] > pontuacoes[1] > 0
    assert np.isnan(pontuacoes[2])
