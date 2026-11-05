import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from src.avaliacao import cenario1, erros_previsao, pares_roc_consumo, pares_roc_gosto, sem_conteudo
from src.metricas import ProtocoloAvaliacao, auc
from src.recomendador import Recomendador


def _locais():
    ids = ["p1", "p2", "p3", "c1", "c2", "c3"]
    return pd.DataFrame(
        {
            "gmap_id": ids,
            "name": [f"Local {i}" for i in ids],
            "cidade": ["X"] * 6,
            "categoria_principal": ["Pizza restaurant"] * 3 + ["Cafe"] * 3,
            "category": [["Pizza restaurant"]] * 3 + [["Cafe"]] * 3,
            "MISC": [{"Amenities": ["Wi-Fi"]}] * 6,
            "latitude": [0.0] * 6,
            "longitude": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "fechado_perm": False,
            "fechado_temp": False,
        }
    )


def _treino():
    linhas = [
        ("ana", "p1", 5), ("ana", "c1", 2), ("ana", "p2", 4),
        ("bia", "c1", 5), ("bia", "c2", 4), ("bia", "p1", 2),
        ("caio", "p3", 4), ("caio", "c3", 5), ("caio", "c2", 3),
    ]
    return pd.DataFrame(linhas, columns=["user_id", "gmap_id", "rating"])


def _alvo():
    linhas = [("ana", "p3", 5), ("ana", "c2", 2), ("bia", "c3", 5), ("bia", "p2", 1), ("caio", "p1", 4)]
    return pd.DataFrame(linhas, columns=["user_id", "gmap_id", "rating"]).assign(segmento="antigo")


def test_sem_conteudo_reescala_os_demais_pesos():
    assert sem_conteudo((0.1, 0.2, 0.5, 0.2)) == pytest.approx((0.0, 2 / 9, 5 / 9, 2 / 9))
    assert sum(sem_conteudo((0.1, 0.2, 0.5, 0.2), 0.8)) == pytest.approx(0.8)


def test_cenario1_avalia_o_modelo_e_as_referencias_no_mesmo_protocolo():
    modelo = Recomendador(percentil=50, centro="fixo", local="cidade").ajustar(_treino(), _locais())
    protocolo, modelos, resultados = cenario1(modelo, _treino(), _alvo(), _locais(), completo=False)
    assert list(resultados)[0] == "modelo"
    assert {"vizinhos por item", "PageRank personalizado", "sem conteúdo"} <= set(resultados)
    assert all(len(resultado.por_usuario) == len(protocolo.usuarios) for resultado in resultados.values())
    esperado = modelo.pontuar(protocolo.usuarios, protocolo.candidatos)
    assert np.allclose(modelos["modelo"](protocolo.usuarios, protocolo.candidatos), esperado)


def _protocolo_pequeno():
    notas = sparse.csr_matrix(np.array([[5, 2, 0, 0], [4, 0, 0, 0]], dtype=float))
    ja_avaliados = sparse.csr_matrix(np.array([[0, 0, 1, 0], [0, 0, 0, 0]], dtype=float))
    return ProtocoloAvaliacao(np.array(["u1", "u2"]), np.array(["a", "b", "c", "d"]), notas, ja_avaliados, np.ones(4), 4)


def test_pares_de_gosto_so_para_quem_tem_notas_boas_e_ruins():
    pontuacoes = np.array([[0.9, 0.1, 0.5, 0.3], [0.2, 0.4, 0.6, 0.8]])
    pares = pares_roc_gosto(_protocolo_pequeno(), pontuacoes)
    assert len(pares) == 1
    rotulos, valores = pares[0]
    assert rotulos.tolist() == [True, False] and valores.tolist() == [0.9, 0.1]


def test_pares_de_consumo_ignoram_ja_avaliados_e_batem_com_a_auc():
    pontuacoes = np.array([[0.9, 0.1, 0.5, 0.3], [0.2, 0.4, 0.6, 0.8]])
    pares = pares_roc_consumo(_protocolo_pequeno(), pontuacoes)
    assert len(pares) == 2
    rotulos, valores = pares[0]
    assert len(rotulos) == 3
    assert auc(valores[rotulos], valores[~rotulos]) == 1.0
    rotulos, valores = pares[1]
    assert auc(valores[rotulos], valores[~rotulos]) == 0.0


def test_erros_de_previsao_ordenam_as_tres_previsoes():
    modelo = Recomendador(percentil=50, centro="fixo", local="cidade").ajustar(_treino(), _locais())
    tabela, contagem = erros_previsao(modelo, _treino(), _alvo())
    assert list(tabela.index) == ["média global", "escore", "escore + viés"]
    assert contagem == {"avaliacoes": 5, "usuarios": 3}
    assert (tabela["RMSE"] ** 2).to_numpy() == pytest.approx(tabela["MSE"].to_numpy())
    assert (tabela["MAE inf"] <= tabela["MAE"]).all() and (tabela["MAE"] <= tabela["MAE sup"]).all()
