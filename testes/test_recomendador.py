import joblib
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from src.traducoes import traduzir_token
from src.recomendador import (
    Recomendador,
    afinidade_cidade,
    afinidade_distancia,
    ajustar_vies_usuarios,
    calcular_componentes,
    coordenadas_completas,
    escolher_pesos,
    escolher_variante,
    escores_de_produto,
    grade_ao_redor,
    grade_de_pesos,
    modelo_ponderado,
    perfis_de_usuarios,
    pontuar,
    prever_nota,
    similaridade_conteudo,
)


def _locais():
    return pd.DataFrame(
        {
            "gmap_id": ["a", "b", "c", "d", "novo", "sem_cidade"],
            "cidade": ["X", "X", "Y", "X", "X", None],
            "fechado_perm": [False, True, False, False, False, False],
            "fechado_temp": False,
            "latitude": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "longitude": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )


def _treino():
    linhas = [("u1", "a", 5), ("u2", "a", 5), ("u3", "a", 5), ("u4", "a", 1), ("u1", "b", 1), ("u2", "b", 3), ("u1", "c", 5), ("u2", "d", 3)]
    return pd.DataFrame(linhas, columns=["user_id", "gmap_id", "rating"])


def test_escore_bayesiano_com_resultado_conhecido():
    tabela, parametros = escores_de_produto(_treino(), _locais())
    media_global = 28 / 8
    assert parametros["C"] == pytest.approx(media_global)
    # Avaliações por local: a=4, b=2, c=1, d=1; a mediana é 1,5.
    assert parametros["m"] == pytest.approx(1.5)
    assert tabela.loc["a", "escore"] == pytest.approx((4 * 4 + 1.5 * media_global) / 5.5)
    assert tabela.loc["a", "escore_normalizado"] == pytest.approx((tabela.loc["a", "escore"] - 1) / 4)


def test_percentil_define_m():
    assert escores_de_produto(_treino(), _locais(), percentil=100)[1]["m"] == 4


def test_local_sem_avaliacoes_recebe_a_media_do_treino():
    tabela, parametros = escores_de_produto(_treino(), _locais())
    assert tabela.loc["novo", "avaliacoes"] == 0
    assert tabela.loc["novo", "escore"] == pytest.approx(parametros["C"])


def test_cidade_pequena_nao_vira_prior_extremo():
    tabela, parametros = escores_de_produto(_treino(), _locais())
    # A cidade Y tem uma única avaliação, com nota 5.
    assert parametros["C"] < tabela.loc["c", "prior_cidade"] < 5
    esperado = (1 * 5 + 1.5 * parametros["C"]) / 2.5
    assert tabela.loc["c", "prior_cidade"] == pytest.approx(esperado)


def test_local_sem_cidade_usa_a_media_do_treino_como_prior():
    tabela, parametros = escores_de_produto(_treino(), _locais())
    assert tabela.loc["sem_cidade", "prior_cidade"] == pytest.approx(parametros["C"])
    assert tabela.loc["sem_cidade", "escore_cidade"] == pytest.approx(parametros["C"])


def test_posicao_na_cidade_so_entre_abertos():
    tabela, _ = escores_de_produto(_treino(), _locais())
    assert np.isnan(tabela.loc["b", "posicao_na_cidade"])
    assert np.isnan(tabela.loc["sem_cidade", "posicao_na_cidade"])
    abertos_em_x = tabela.loc[["a", "d", "novo"], "posicao_na_cidade"]
    assert sorted(abertos_em_x.tolist()) == [1, 2, 3]
    assert tabela.loc["c", "posicao_na_cidade"] == 1


def test_popularidade_com_resultado_conhecido():
    tabela, _ = escores_de_produto(_treino(), _locais())
    assert tabela.loc["a", "popularidade"] == pytest.approx(1)
    assert tabela.loc["b", "popularidade"] == pytest.approx(np.log(3) / np.log(5))


def test_local_novo_recebe_a_mediana_da_cidade_ou_do_catalogo():
    tabela, _ = escores_de_produto(_treino(), _locais())
    em_x = tabela.loc[["a", "b", "d"], "popularidade"].median()
    assert tabela.loc["novo", "popularidade"] == pytest.approx(em_x)
    catalogo = tabela.loc[["a", "b", "c", "d"], "popularidade"].median()
    assert tabela.loc["sem_cidade", "popularidade"] == pytest.approx(catalogo)


def _vetores():
    return sparse.csr_matrix(np.array([[1.0, 0], [0, 1.0], [1.0, 0], [0, 1.0]]))


POSICAO = {"a": 0, "b": 1, "c": 2, "d": 3}


def _perfil(notas, centro="fixo"):
    treino = pd.DataFrame(
        {"user_id": "u", "gmap_id": list(notas), "rating": list(notas.values())}
    )
    return perfis_de_usuarios(treino, _vetores(), POSICAO, centro=centro)[0].toarray()[0]


def test_perfil_ponderado_pela_nota():
    # Pesos: a = +2 e b = -1, então o vetor é (2, -1), normalizado.
    assert _perfil({"a": 5, "b": 2}) == pytest.approx(np.array([2, -1]) / np.sqrt(5))


def test_perfil_so_com_notas_neutras_usa_a_media_simples():
    assert _perfil({"a": 3, "b": 3}) == pytest.approx(np.array([1, 1]) / np.sqrt(2))


def test_perfil_com_pesos_opostos_vira_vetor_nulo_e_similaridade_neutra():
    # a e c têm o mesmo vetor, com pesos +2 e -2.
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a", "c"], "rating": [5, 1]})
    perfis, _ = perfis_de_usuarios(treino, _vetores(), POSICAO)
    assert perfis.nnz == 0
    assert similaridade_conteudo(perfis, _vetores()).tolist() == [[0.5, 0.5, 0.5, 0.5]]


def test_centro_pela_media_do_usuario():
    # Média 3,5: pesos a = +1,5 e b = -1,5.
    assert _perfil({"a": 5, "b": 2}, centro="usuario") == pytest.approx(np.array([1, -1]) / np.sqrt(2))


def test_centro_pela_media_usa_3_para_quem_nao_varia():
    assert _perfil({"a": 5, "b": 5}, centro="usuario") == pytest.approx(_perfil({"a": 5, "b": 5}))


def test_centro_desconhecido_gera_erro():
    with pytest.raises(ValueError):
        _perfil({"a": 5}, centro="outro")


def test_similaridade_vai_de_zero_a_um():
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a", "b"], "rating": [5, 1]})
    perfis, usuarios = perfis_de_usuarios(treino, _vetores(), POSICAO)
    assert usuarios.tolist() == ["u"]
    sims = similaridade_conteudo(perfis, _vetores())
    assert sims[0, 0] == pytest.approx((1 / np.sqrt(2) + 1) / 2)
    assert sims[0, 1] == pytest.approx((-1 / np.sqrt(2) + 1) / 2)


def test_vetor_vazio_do_local_da_similaridade_neutra():
    vetores = sparse.csr_matrix(np.array([[1.0, 0], [0, 0.0]]))
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a"], "rating": [5]})
    perfis, _ = perfis_de_usuarios(treino, vetores, {"a": 0, "b": 1})
    assert similaridade_conteudo(perfis, vetores)[0, 1] == 0.5


def test_afinidade_cidade_com_resultado_conhecido():
    # u1 avaliou a e b em X e c em Y.
    resultado = afinidade_cidade(_treino(), _locais(), ["u1", "inexistente"], ["a", "c", "sem_cidade"])
    assert resultado[0].tolist() == pytest.approx([2 / 3, 1 / 3, 0])
    assert resultado[1].tolist() == [0, 0, 0]


def test_afinidade_cidade_conta_quem_avaliou_local_sem_cidade_no_total():
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a", "sem_cidade"], "rating": [5, 5]})
    assert afinidade_cidade(treino, _locais(), ["u"], ["d"])[0, 0] == pytest.approx(0.5)


def test_afinidade_distancia_com_distancia_conhecida():
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a"], "rating": [5]})
    # Um grau de longitude no equador tem cerca de 111,19 km.
    resultado = afinidade_distancia(treino, _locais(), ["u", "inexistente"], ["a", "b"], tau=50)
    assert resultado[0, 0] == pytest.approx(1)
    assert resultado[0, 1] == pytest.approx(np.exp(-111.19 / 50), abs=1e-3)
    assert resultado[1].tolist() == [0, 0]


def test_afinidade_distancia_faz_a_media_entre_os_avaliados():
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a", "b"], "rating": [5, 1]})
    resultado = afinidade_distancia(treino, _locais(), ["u"], ["a"], tau=50)
    assert resultado[0, 0] == pytest.approx((1 + np.exp(-111.19 / 50)) / 2, abs=1e-3)


def test_coordenadas_faltantes_usam_a_cidade_e_depois_ficam_vazias():
    locais = pd.DataFrame(
        {
            "cidade": ["X", "X", "X", None],
            "latitude": [1.0, 3.0, np.nan, np.nan],
            "longitude": [10.0, 30.0, np.nan, np.nan],
        }
    )
    coordenadas = coordenadas_completas(locais)
    assert coordenadas[2].tolist() == [2, 20]
    assert np.isnan(coordenadas[3]).all()


def test_afinidade_distancia_sem_coordenada_nem_cidade_vale_zero():
    locais = _locais()
    locais.loc[locais["gmap_id"] == "sem_cidade", ["latitude", "longitude"]] = np.nan
    treino = pd.DataFrame({"user_id": "u", "gmap_id": ["a"], "rating": [5]})
    assert afinidade_distancia(treino, locais, ["u"], ["sem_cidade"], tau=50)[0, 0] == 0


def test_pontuacao_com_resultado_conhecido():
    componentes = {
        "conteudo": np.array([[0.5, 1.0]]),
        "escore": np.array([0.8, 0.4]),
        "local": np.array([[1.0, 0.0]]),
        "popularidade": np.array([0.2, 0.6]),
    }
    resultado = pontuar(componentes, (0.1, 0.2, 0.5, 0.2))
    assert resultado[0].tolist() == pytest.approx([0.05 + 0.16 + 0.5 + 0.04, 0.1 + 0.08 + 0 + 0.12])
    assert modelo_ponderado(componentes, (1, 0, 0, 0))(None, None).tolist() == [[0.5, 1.0]]


def test_grade_tem_286_combinacoes_que_somam_1():
    grade = grade_de_pesos(0.1)
    assert len(grade) == 286
    assert len(set(grade)) == 286
    assert all(sum(pesos) == pytest.approx(1) and min(pesos) >= 0 for pesos in grade)
    assert (0.1, 0.2, 0.5, 0.2) in grade


def test_grade_ao_redor_respeita_raio_e_alfa_minimo():
    grade = grade_ao_redor((0.1, 0.2, 0.5, 0.2))
    assert (0.1, 0.2, 0.5, 0.2) in grade
    assert (0.15, 0.2, 0.45, 0.2) in grade
    assert all(pesos[0] >= 0.1 and abs(pesos[2] - 0.5) <= 0.1 + 1e-9 and sum(pesos) == pytest.approx(1) for pesos in grade)
    assert (0.05, 0.25, 0.5, 0.2) not in grade


def _grade():
    return pd.DataFrame(
        [
            {"alfa": 0.0, "conversao": 0.10, "auc_gosto": 0.9},
            {"alfa": 0.1, "conversao": 0.06, "auc_gosto": 0.5},
            {"alfa": 0.1, "conversao": 0.058, "auc_gosto": 0.6},
            {"alfa": 0.2, "conversao": 0.05, "auc_gosto": 0.8},
        ]
    )


def test_criterio_escolhe_maior_gosto_entre_as_aptas_com_alfa_minimo():
    # Entre alfa >= 0,1, a melhor conversão é 0,06; com 95%, entram 0,06 e 0,058.
    assert escolher_pesos(_grade())["auc_gosto"] == 0.6


def test_criterio_com_outro_limiar():
    assert escolher_pesos(_grade(), limiar=0.8)["auc_gosto"] == 0.8


def test_criterio_sem_alfa_minimo_considera_todas():
    assert escolher_pesos(_grade(), alfa_minimo=0)["auc_gosto"] == 0.9


class _Resultado:
    def __init__(self, conversao, gosto):
        self.por_usuario = pd.DataFrame({"conversao": [conversao], "auc_gosto": [gosto]})


def test_variante_troca_so_se_a_melhora_de_gosto_nao_for_empate():
    resultados = {"base": _Resultado(0.10, 0.5), "outra": _Resultado(0.10, 0.6)}
    sem_empate = lambda a, b, metrica: {"empate": False}
    com_empate = lambda a, b, metrica: {"empate": True}
    assert escolher_variante(resultados, "base", sem_empate) == "outra"
    assert escolher_variante(resultados, "base", com_empate) == "base"


def test_variante_com_conversao_baixa_nao_e_apta():
    resultados = {"base": _Resultado(0.10, 0.5), "outra": _Resultado(0.05, 0.9)}
    assert escolher_variante(resultados, "base", lambda a, b, metrica: {"empate": False}) == "base"


def test_calcular_componentes_alinha_usuarios_e_candidatos():
    locais = _locais().assign(category=[["Bar"], ["Bar"], ["Pub"], ["Pub"], ["Bar"], ["Pub"]], MISC=[{"Amenities": ["Wi-Fi"]}] * 6)
    resultado = calcular_componentes(_treino(), locais, np.array(["u1", "desconhecido"]), np.array(["a", "c", "novo"]))
    assert resultado["conteudo"].shape == (2, 3)
    assert resultado["conteudo"][1].tolist() == [0.5, 0.5, 0.5]
    assert resultado["escore"].shape == (3,)
    assert resultado["local"][0].tolist() == pytest.approx([2 / 3, 1 / 3, 2 / 3])
    assert resultado["local"][1].tolist() == [0, 0, 0]


def test_calcular_componentes_com_outro_local():
    locais = _locais().assign(category=[["Bar"], ["Bar"], ["Pub"], ["Pub"], ["Bar"], ["Pub"]], MISC=[{"Amenities": ["Wi-Fi"]}] * 6)
    usuarios, candidatos = np.array(["u1"]), np.array(["a"])
    cidade = calcular_componentes(_treino(), locais, usuarios, candidatos)["local"]
    distancia = calcular_componentes(_treino(), locais, usuarios, candidatos, local="distancia", tau=50)["local"]
    media = calcular_componentes(_treino(), locais, usuarios, candidatos, local="media", tau=50)["local"]
    assert media[0, 0] == pytest.approx((cidade[0, 0] + distancia[0, 0]) / 2)
    with pytest.raises(ValueError):
        calcular_componentes(_treino(), locais, usuarios, candidatos, local="outro")


def test_vies_regularizado_com_resultado_conhecido():
    treino = pd.DataFrame({"user_id": ["u", "u"], "gmap_id": ["a", "b"], "rating": [5, 4]})
    escores = pd.Series({"a": 4.0, "b": 4.0})
    assert ajustar_vies_usuarios(treino, escores, reg=2)["u"] == pytest.approx(1 / 4)


def test_previsao_soma_vies_limita_e_ignora_usuario_sem_historico():
    escores = pd.Series({"a": 4.0, "b": 1.5})
    vies = pd.Series({"u": 2.0, "v": -1.0})
    resultado = prever_nota(["u", "v", "novo"], ["a", "b", "a"], escores, vies)
    assert resultado.tolist() == [5, 1, 4]


def _locais_modelo():
    return pd.DataFrame(
        {
            "gmap_id": ["pizza1", "pizza2", "cafe1", "cafe2", "fechado", "novo_real", "longe"],
            "name": ["Pizza Um", "Pizza Dois", "Café Um", "Café Dois", "Fechado", "Novo", "Longe"],
            "cidade": ["X", "X", "X", "X", "X", "X", "Z"],
            "categoria_principal": ["Pizza restaurant"] * 2 + ["Cafe"] * 2 + ["Bar", "Bar", "Bar"],
            "category": [["Pizza restaurant"], ["Pizza restaurant"], ["Cafe"], ["Cafe"], ["Pizza restaurant"], ["Cafe"], ["Cafe"]],
            "MISC": [{"Amenities": ["Wi-Fi"]}] * 7,
            "latitude": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "longitude": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 9.0],
            "fechado_perm": [False, False, False, False, True, False, False],
            "fechado_temp": False,
        }
    )


def _treino_modelo():
    linhas = [
        ("ana", "pizza1", 5),
        ("ana", "cafe1", 1),
        ("ana", "fechado", 4),
        ("bia", "pizza1", 4),
        ("bia", "pizza2", 5),
        ("bia", "cafe2", 5),
        ("bia", "longe", 2),
        ("caio", "cafe1", 5),
    ]
    return pd.DataFrame(linhas, columns=["user_id", "gmap_id", "rating"])


def _modelo(**opcoes):
    return Recomendador(percentil=50, centro="fixo", local="cidade", **opcoes).ajustar(_treino_modelo(), _locais_modelo())


def test_classe_aplica_a_formula_da_pontuacao():
    modelo = _modelo(pesos=(0.1, 0.2, 0.5, 0.2))
    candidatos = np.array(["pizza2", "cafe2"])
    componentes = modelo.componentes(["ana"], candidatos)
    esperado = (
        0.1 * componentes["conteudo"][0]
        + 0.2 * componentes["escore"]
        + 0.5 * componentes["local"][0]
        + 0.2 * componentes["popularidade"]
    )
    assert modelo.pontuar(["ana"], candidatos)[0] == pytest.approx(esperado)


def test_recomendar_tira_fechados_avaliados_e_locais_fora_do_treino():
    tabela = _modelo().recomendar("ana", n=10)
    assert set(tabela["gmap_id"]) == {"pizza2", "cafe2", "longe"}


def test_recomendar_ordena_e_respeita_n():
    tabela = _modelo().recomendar("ana", n=2)
    assert len(tabela) == 2
    assert tabela["pontuacao"].is_monotonic_decreasing
    assert {"nome", "cidade", "conteudo", "escore", "local", "popularidade", "explicacao"} <= set(tabela.columns)


def test_usuario_com_uma_avaliacao_usa_o_mesmo_fluxo():
    assert "cafe1" not in set(_modelo().recomendar("caio")["gmap_id"])


def test_usuario_inexistente_gera_erro():
    with pytest.raises(ValueError):
        _modelo().recomendar("ninguem")
    with pytest.raises(ValueError):
        _modelo().explicar("ninguem", "pizza1")


def test_explicacao_aponta_o_local_bem_avaliado_mais_parecido():
    explicacao = _modelo().explicar("ana", "pizza2")
    assert explicacao["parecido"]["nome"] == "Pizza Um"
    assert explicacao["parecido"]["nota"] == 5
    assert "Pizza Um" in explicacao["frase"]
    assert "Pizzaria" in explicacao["tokens"]
    assert len(explicacao["tokens"]) <= 3


def test_explicacao_nao_usa_o_que_o_usuario_nao_gostou():
    # O único café de ana tem nota 1, e o local com nota 4 é uma pizzaria fechada.
    explicacao = _modelo().explicar("ana", "cafe2")
    assert explicacao["parecido"]["nome"] != "Café Um"
    assert "Cafeteria" not in explicacao["tokens"]


def test_explicacao_sem_local_parecido_ainda_tem_frase():
    treino = pd.DataFrame({"user_id": ["u", "u", "v", "v"], "gmap_id": ["pizza1", "pizza2", "cafe1", "cafe2"], "rating": [3, 3, 5, 5]})
    modelo = Recomendador(percentil=50, centro="fixo", local="cidade").ajustar(treino, _locais_modelo())
    explicacao = modelo.explicar("u", "cafe1")
    assert explicacao["parecido"] is None
    assert explicacao["frase"]


def test_token_sem_traducao_nao_aparece():
    assert traduzir_token("cat=pizza_restaurant") == "Pizzaria"
    assert traduzir_token("misc=service_options:delivery") == "Entrega"
    assert traduzir_token("cat=categoria_inventada") is None


def test_prever_nota_da_classe_usa_escore_e_vies():
    modelo = _modelo()
    previsao = modelo.prever_nota(["ana", "ninguem"], ["pizza2", "pizza2"])
    assert previsao[1] == pytest.approx(modelo.escores.loc["pizza2", "escore"])
    assert 1 <= previsao[0] <= 5


def test_usuario_novo_com_cidade_prefere_a_cidade():
    tabela = _modelo(pesos_usuario_novo=(0.0, 0.0, 1.0, 0.0)).recomendar_usuario_novo(cidade="Z", n=1)
    assert tabela["gmap_id"].tolist() == ["longe"]


def test_usuario_novo_sem_informacao_tambem_recebe_lista():
    tabela = _modelo().recomendar_usuario_novo(n=3)
    assert len(tabela) == 3
    assert "fechado" not in set(tabela["gmap_id"])


def test_usuario_novo_com_categoria_ou_exemplo_usa_conteudo():
    modelo = _modelo(pesos_usuario_novo=(1.0, 0.0, 0.0, 0.0))
    assert modelo.recomendar_usuario_novo(categorias=["Cafe"], n=1)["categoria_principal"].iloc[0] == "Cafe"
    tabela = modelo.recomendar_usuario_novo(local_exemplo="pizza1", n=1)
    assert tabela["gmap_id"].tolist() == ["pizza2"]


def test_usuario_novo_com_cidade_inexistente_gera_erro():
    with pytest.raises(ValueError):
        _modelo().recomendar_usuario_novo(cidade="Atlantida")


def test_usuarios_para_local_novo_com_cadastro_manual():
    cadastro = {"category": ["Pizza restaurant"], "MISC": {}, "cidade": "X", "latitude": 0.0, "longitude": 0.0}
    tabela = _modelo(pesos_local_novo=(1.0, 0.0)).usuarios_para_local_novo(cadastro, n=5)
    # Só ana e bia têm 3 ou mais avaliações, e ana é a que mais favorece pizza.
    assert set(tabela["user_id"]) == {"ana", "bia"}
    assert tabela["pontuacao"].is_monotonic_decreasing


def test_afinidade_de_local_novo_usa_a_cidade_do_cadastro():
    cadastro = {"category": ["Cafe"], "MISC": {}, "cidade": "Z"}
    tabela = _modelo(pesos_local_novo=(0.0, 1.0)).usuarios_para_local_novo(cadastro, n=5)
    assert tabela.set_index("user_id").loc["bia", "local"] == pytest.approx(1 / 4)
    assert tabela.set_index("user_id").loc["ana", "local"] == 0


def test_posicao_de_local_novo_e_decisao_de_recomendar():
    modelo = _modelo()
    cadastro = {"category": ["Pizza restaurant"], "MISC": {}, "cidade": "X"}
    resultado = modelo.posicao_local_novo("ana", cadastro, n=10)
    assert 1 <= resultado["posicao"] <= resultado["total"]
    assert resultado["total"] == 4
    assert resultado["recomendar"] is True
    assert modelo.posicao_local_novo("ana", cadastro, n=0)["recomendar"] is False


def test_local_novo_recebe_mediana_de_popularidade_e_nao_e_penalizado():
    modelo = _modelo()
    assert modelo._popularidade_de_local_novo("X") > 0
    assert modelo._popularidade_de_local_novo("cidade_sem_locais") > 0


def test_recomendador_salvo_reproduz_a_lista(tmp_path):
    modelo = _modelo()
    caminho = tmp_path / "modelo.joblib"
    joblib.dump(modelo, caminho)
    carregado = joblib.load(caminho)
    pd.testing.assert_frame_equal(carregado.recomendar("ana"), modelo.recomendar("ana"))


def _cadastros(**colunas):
    return pd.DataFrame(colunas)


def test_componentes_de_cadastros_seguem_a_lista_individual():
    modelo = _modelo(pesos_usuario_novo=(0.2, 0.3, 0.4, 0.1))
    candidatos = np.array(["pizza1", "pizza2", "cafe1", "cafe2", "longe"])
    cadastros = _cadastros(cidade=["Z", None], categorias=[["Cafe"], None], local_exemplo=[None, "pizza1"])
    lote = pontuar(modelo.componentes_cadastros(cadastros, candidatos), modelo.pesos_usuario_novo)
    for i, (cidade, categorias, exemplo) in enumerate([("Z", ["Cafe"], None), (None, None, "pizza1")]):
        tabela = modelo.recomendar_usuario_novo(cidade=cidade, categorias=categorias, local_exemplo=exemplo, n=10)
        esperado = dict(zip(candidatos, lote[i]))
        for gmap_id, pontuacao in zip(tabela["gmap_id"], tabela["pontuacao"]):
            assert pontuacao == pytest.approx(esperado[gmap_id])


def test_cadastro_sem_nada_tem_conteudo_neutro_e_local_zero():
    modelo = _modelo()
    componentes = modelo.componentes_cadastros(_cadastros(cidade=[None]), ["pizza1", "cafe1"])
    assert np.allclose(componentes["conteudo"], 0.5)
    assert np.allclose(componentes["local"], 0)


def test_categoria_declarada_e_local_de_exemplo_somam_no_vetor():
    modelo = _modelo()
    candidatos = ["pizza2", "cafe2"]
    so_categoria = modelo.componentes_cadastros(_cadastros(categorias=[["Cafe"]]), candidatos)["conteudo"][0]
    so_exemplo = modelo.componentes_cadastros(_cadastros(local_exemplo=["pizza1"]), candidatos)["conteudo"][0]
    os_dois = modelo.componentes_cadastros(_cadastros(categorias=[["Cafe"]], local_exemplo=["pizza1"]), candidatos)["conteudo"][0]
    assert so_categoria[1] > so_categoria[0]
    assert so_exemplo[0] > so_exemplo[1]
    # Os dois juntos ficam entre os extremos de cada um.
    assert so_categoria[0] < os_dois[0] < so_exemplo[0]


def test_local_de_exemplo_desconhecido_gera_erro():
    with pytest.raises(ValueError):
        _modelo().componentes_cadastros(_cadastros(local_exemplo=["inexistente"]), ["pizza1"])


def test_coincidencia_de_categorias():
    modelo = _modelo()
    matriz = modelo.coincidencia_de_categorias(_cadastros(categorias=[["Cafe"], [], None]), ["pizza1", "cafe1", "longe"])
    assert matriz.tolist() == [[0, 1, 1], [0, 0, 0], [0, 0, 0]]


def test_filtro_de_categorias_poe_as_declaradas_primeiro_e_completa_a_lista():
    modelo = _modelo(pesos_usuario_novo=(0.0, 0.0, 0.0, 1.0))
    tabela = modelo.recomendar_usuario_novo(categorias=["Pizza restaurant"], n=4, filtrar_categorias=True)
    assert len(tabela) == 4
    assert set(tabela["gmap_id"].iloc[:2]) == {"pizza1", "pizza2"}
    assert any("categorias" in aviso for aviso in tabela.attrs["avisos"])


def test_filtro_de_preco_e_ignorado_se_sobrar_pouco():
    locais = _locais_modelo().assign(preco_nivel=[1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    modelo = Recomendador(percentil=50, centro="fixo", local="cidade").ajustar(_treino_modelo(), locais)
    filtrada = modelo.recomendar_usuario_novo(preco=1, n=2)
    assert "pizza2" not in set(filtrada["gmap_id"]) and filtrada.attrs["avisos"] == []
    ignorado = modelo.recomendar_usuario_novo(preco=2, n=2)
    assert len(ignorado) == 2
    assert any("preço" in aviso for aviso in ignorado.attrs["avisos"])


def test_cidade_com_poucos_locais_avisa_e_nao_esvazia():
    tabela = _modelo().recomendar_usuario_novo(cidade="Z", n=3)
    assert len(tabela) == 3
    assert any("ampliada" in aviso for aviso in tabela.attrs["avisos"])
