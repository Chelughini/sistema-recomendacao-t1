import numpy as np
import pandas as pd
import pytest

from src.analises import (
    ajustar_vieses,
    decompor_variancia,
    distancia_ao_mais_proximo,
    erros_de_nota,
    ic_bootstrap,
    k_core,
    matriz_binaria,
    matriz_distancias_km,
    matriz_jaccard,
    media_entre_pares,
    suporte_vizinhos,
)


def _avaliacoes(pares):
    return pd.DataFrame(pares, columns=["user_id", "gmap_id"])


def test_k_core_remove_em_cascata():
    avaliacoes = _avaliacoes(
        [("a", "x"), ("a", "y"), ("b", "x"), ("b", "y"), ("c", "x"), ("c", "z"), ("d", "z")]
    )
    nucleo = k_core(avaliacoes, 2)
    assert set(nucleo["user_id"]) == {"a", "b"}
    assert set(nucleo["gmap_id"]) == {"x", "y"}


def test_k_core_com_k_1_mantem_tudo():
    avaliacoes = _avaliacoes([("a", "x"), ("b", "y")])
    assert len(k_core(avaliacoes, 1)) == 2


def test_matriz_binaria_ignora_repeticao():
    matriz = matriz_binaria(["a", "a", "b"], ["x", "x", "y"])
    assert matriz.shape == (2, 2)
    assert matriz.toarray().tolist() == [[1, 0], [0, 1]]


def test_suporte_vizinhos_exclui_a_propria_linha():
    matriz = matriz_binaria(["a", "a", "a", "b", "b", "b", "c", "c", "c"], ["x", "y", "z", "x", "y", "w", "x", "k", "m"])
    resultado = suporte_vizinhos(matriz, [0], minimos=(1, 2), posicao=2)
    assert resultado.loc[0, "vizinhos_1+"] == 2
    assert resultado.loc[0, "vizinhos_2+"] == 1
    assert resultado.loc[0, "suporte_vizinho"] == 1


def test_suporte_vizinhos_sem_vizinhos_suficientes_vale_zero():
    matriz = matriz_binaria(["a", "b"], ["x", "x"])
    assert suporte_vizinhos(matriz, [0], minimos=(1,), posicao=5).loc[0, "suporte_vizinho"] == 0


def test_decomposicao_em_dados_aditivos_explica_tudo():
    linhas = []
    for u, vies_u in enumerate([0, 1]):
        for i, vies_i in enumerate([0, 2]):
            linhas.append({"user_id": u, "gmap_id": i, "rating": 1 + vies_u + vies_i})
    resultado = decompor_variancia(pd.DataFrame(linhas))
    assert resultado["local_usuario"] == pytest.approx(1)
    assert resultado["local"] == pytest.approx(0.8)


def test_decomposicao_sem_efeito_de_local_vale_zero():
    tabela = pd.DataFrame(
        {"user_id": [1, 2, 3, 4], "gmap_id": ["x", "x", "y", "y"], "rating": [1, 5, 1, 5]}
    )
    assert decompor_variancia(tabela)["local"] == pytest.approx(0)


def test_jaccard_com_resultados_conhecidos():
    matriz = matriz_jaccard([["a", "b"], ["b", "c"], ["d"]])
    assert matriz[0, 1] == pytest.approx(1 / 3)
    assert matriz[0, 2] == 0
    assert matriz[0, 0] == 1


def test_media_entre_pares_ignora_a_diagonal():
    matriz = np.array([[1.0, 0.5, 0.0], [0.5, 1.0, 0.25], [0.0, 0.25, 1.0]])
    assert media_entre_pares(matriz, [0, 1, 2]) == pytest.approx(0.25)
    assert media_entre_pares(matriz, [0, 1]) == pytest.approx(0.5)


def test_haversine_com_distancia_conhecida():
    distancias = matriz_distancias_km([0, 0, 41.14], [0, 1, -104.82])
    assert distancias[0, 1] == pytest.approx(111.19, abs=0.01)
    assert distancias[0, 0] == 0
    assert distancias[1, 0] == pytest.approx(distancias[0, 1])


def test_distancia_ao_mais_proximo_olha_so_o_passado():
    distancias = np.array([[0, 10, 100.0], [10, 0, 50.0], [100, 50, 0.0]])
    avaliacoes = pd.DataFrame(
        {
            "user_id": ["u", "u", "u", "v"],
            "gmap_id": ["c", "a", "b", "a"],
            "data": pd.to_datetime(["2020-01-03", "2020-01-01", "2020-01-02", "2020-01-01"]),
        }
    )
    resultado = distancia_ao_mais_proximo(avaliacoes, {"a": 0, "b": 1, "c": 2}, distancias)
    assert sorted(resultado.tolist()) == [10.0, 50.0]


def test_ic_bootstrap_contem_a_media_e_e_reproduzivel():
    valores = np.arange(100.0)
    media, inferior, superior = ic_bootstrap(valores, reamostragens=300)
    assert media == pytest.approx(49.5)
    assert inferior < media < superior
    assert ic_bootstrap(valores, reamostragens=300) == (media, inferior, superior)


def test_ic_bootstrap_por_grupo_usa_a_media_de_todas_as_linhas():
    media, inferior, superior = ic_bootstrap([1, 1, 1, 5], grupos=["a", "a", "a", "b"], reamostragens=200)
    assert media == pytest.approx(2)
    assert inferior >= 1
    assert superior <= 5


def test_vieses_recuperam_a_direcao_e_encolhem():
    treino = pd.DataFrame(
        {
            "user_id": ["a"] * 4 + ["b"] * 4,
            "gmap_id": ["x", "y"] * 4,
            "rating": [5, 3, 5, 3, 4, 2, 4, 2],
        }
    )
    media, vies_usuario, vies_local = ajustar_vieses(treino, reg=1)
    assert media == pytest.approx(3.5)
    assert vies_local["x"] > 0 > vies_local["y"]
    assert vies_usuario["a"] > 0 > vies_usuario["b"]
    assert abs(vies_local["x"]) < 1


def test_erros_de_nota_com_resultado_conhecido():
    resultado = erros_de_nota([1, 5], [2, 2])
    assert resultado["MAE"] == 2
    assert resultado["MSE"] == 5
    assert resultado["RMSE"] == pytest.approx(np.sqrt(5))
