import pandas as pd

from src.divisao import (
    calcular_cortes,
    dividir_temporal,
    eh_relevante,
    locais_novos_naturais,
    montar_conjuntos,
    retirar_locais,
    segmentar,
    simular_cadastros,
    sortear_locais_simulados,
)


def _base():
    """Dez avaliações por ano, de 2010 a 2020, em que o quantil 80% cai em 01/01/2018."""
    datas = pd.date_range("2010-01-01", "2020-01-01", freq="YS")
    return pd.DataFrame({"data": datas, "rating": range(len(datas)), "user_id": "u", "gmap_id": "x"})


def test_cortes_com_resultado_conhecido():
    corte_teste, corte_validacao = calcular_cortes(_base())
    assert corte_teste == pd.Timestamp("2018-01-01")
    assert corte_validacao == pd.Timestamp("2017-01-01")


def test_corte_de_validacao_e_exatamente_um_ano_antes_mesmo_em_ano_bissexto():
    base = pd.DataFrame({"data": [pd.Timestamp("2020-02-29")] * 2})
    corte_teste, corte_validacao = calcular_cortes(base)
    assert corte_teste == pd.Timestamp("2020-02-29")
    assert corte_validacao == pd.Timestamp("2019-02-28")


def test_cada_corte_pertence_ao_periodo_que_comeca_nele():
    particoes = dividir_temporal(_base())
    assert particoes["treino"]["data"].max() == pd.Timestamp("2016-01-01")
    assert particoes["validacao"]["data"].tolist() == [pd.Timestamp("2017-01-01")]
    assert particoes["teste"]["data"].min() == pd.Timestamp("2018-01-01")


def test_contagens_fecham_e_datas_nao_se_sobrepoem():
    base = _base()
    particoes = dividir_temporal(base)
    assert len(particoes["treino"]) + len(particoes["validacao"]) == len(particoes["treino_total"])
    assert len(particoes["treino_total"]) + len(particoes["teste"]) == len(base)
    assert particoes["treino"]["data"].max() < particoes["validacao"]["data"].min()
    assert particoes["validacao"]["data"].max() < particoes["teste"]["data"].min()


def test_treino_total_e_a_uniao_de_treino_e_validacao():
    particoes = dividir_temporal(_base())
    unidos = pd.concat([particoes["treino"], particoes["validacao"]]).sort_index()
    pd.testing.assert_frame_equal(unidos, particoes["treino_total"])


def test_divisao_e_reproduzivel_e_nao_altera_a_entrada():
    base = _base()
    copia = base.copy()
    primeira, segunda = dividir_temporal(base), dividir_temporal(base)
    for nome in primeira:
        pd.testing.assert_frame_equal(primeira[nome], segunda[nome])
    pd.testing.assert_frame_equal(base, copia)


def test_relevante_e_nota_4_ou_maior():
    assert eh_relevante(pd.Series([1, 2, 3, 4, 5])).tolist() == [False, False, False, True, True]


def test_segmentos_conforme_o_historico_no_treino():
    treino = pd.DataFrame({"user_id": ["a", "a", "a", "b", "c", "c"]})
    alvo = pd.DataFrame({"user_id": ["a", "b", "c", "d"]})
    resultado = segmentar(alvo, treino)
    assert resultado["segmento"].tolist() == ["antigo", "intermediario", "intermediario", "novo"]
    assert resultado["avaliacoes_no_treino"].tolist() == [3, 1, 2, 0]


def test_segmentar_com_sufixo_nao_sobrescreve_o_outro_treino():
    alvo = pd.DataFrame({"user_id": ["a"]})
    resultado = segmentar(segmentar(alvo, pd.DataFrame({"user_id": ["a"] * 3})), pd.DataFrame({"user_id": ["a"]}), "_c3")
    assert resultado.loc[0, "segmento"] == "antigo"
    assert resultado.loc[0, "segmento_c3"] == "intermediario"


def test_locais_naturais_sao_os_ausentes_do_treino():
    treino = pd.DataFrame({"gmap_id": ["a", "b"]})
    alvo = pd.DataFrame({"gmap_id": ["z", "b", "c", "z"]})
    assert locais_novos_naturais(alvo, treino).tolist() == ["c", "z"]


def _locais(**fechados):
    nomes = ["a", "b", "c", "d", "e"]
    return pd.DataFrame(
        {
            "gmap_id": nomes,
            "fechado_perm": [nome in fechados.get("perm", "") for nome in nomes],
            "fechado_temp": [nome in fechados.get("temp", "") for nome in nomes],
        }
    )


def test_simulados_sao_abertos_com_o_minimo_de_avaliacoes():
    treino = pd.DataFrame({"gmap_id": ["a"] * 3 + ["b"] * 3 + ["c"] * 3 + ["d"] * 3 + ["e"] * 2})
    escolhidos = sortear_locais_simulados(treino, _locais(perm="a", temp="b"), quantidade=2, minimo_avaliacoes=3)
    assert sorted(escolhidos.tolist()) == ["c", "d"]


def test_simulados_respeitam_a_exclusao_e_sao_reproduziveis():
    treino = pd.DataFrame({"gmap_id": ["a", "b", "c", "d", "e"] * 3})
    primeiro = sortear_locais_simulados(treino, _locais(), quantidade=2, minimo_avaliacoes=3, excluir=["a", "b"])
    segundo = sortear_locais_simulados(treino, _locais(), quantidade=2, minimo_avaliacoes=3, excluir=["a", "b"])
    assert primeiro.tolist() == segundo.tolist()
    assert not {"a", "b"} & set(primeiro)


def test_retirar_locais_remove_so_os_informados():
    treino = pd.DataFrame({"gmap_id": ["a", "b", "a"]})
    assert retirar_locais(treino, ["a"])["gmap_id"].tolist() == ["b"]


def _base_com_cenarios():
    """Locais de a até e no passado, x só na validação e y só no teste; `u` tem histórico e `v` só aparece no alvo."""
    linhas = []
    for dia, gmap_id in enumerate(["a", "b", "c", "d", "e"] * 6):
        linhas.append({"user_id": "u", "gmap_id": gmap_id, "rating": 5, "data": pd.Timestamp("2015-01-01") + pd.Timedelta(days=dia)})
    for dia in range(5):
        linhas.append({"user_id": "v", "gmap_id": "x", "rating": 4, "data": pd.Timestamp("2019-06-01") + pd.Timedelta(days=dia)})
        linhas.append({"user_id": "u", "gmap_id": "a", "rating": 4, "data": pd.Timestamp("2019-07-01") + pd.Timedelta(days=dia)})
    for dia in range(5):
        linhas.append({"user_id": "w", "gmap_id": "y", "rating": 3, "data": pd.Timestamp("2020-06-01") + pd.Timedelta(days=dia)})
        linhas.append({"user_id": "u", "gmap_id": "b", "rating": 3, "data": pd.Timestamp("2020-07-01") + pd.Timedelta(days=dia)})
    return pd.DataFrame(linhas)


def _conjuntos_pequenos():
    base = _base_com_cenarios()
    locais = pd.DataFrame(
        {"gmap_id": ["a", "b", "c", "d", "e", "x", "y"], "fechado_perm": False, "fechado_temp": False}
    )
    return base, montar_conjuntos(base, locais, quantidade=1, minimo_avaliacoes=5)


def test_conjuntos_simulados_sao_disjuntos_e_fora_do_treino_correspondente():
    _, conjuntos = _conjuntos_pequenos()
    novos = conjuntos["locais_novos"]
    simulados = novos[novos["origem"] == "simulado"]
    s_val = set(simulados.loc[simulados["conjunto"] == "validacao", "gmap_id"])
    s_teste = set(simulados.loc[simulados["conjunto"] == "teste", "gmap_id"])
    assert len(s_val) == len(s_teste) == 1
    assert not s_val & s_teste
    assert not s_val & set(conjuntos["treino_c3"]["gmap_id"])
    assert not s_teste & set(conjuntos["treino_total_c3"]["gmap_id"])
    assert s_val <= set(conjuntos["treino_total_c3"]["gmap_id"])


def test_conjuntos_nao_mudam_os_treinos_dos_cenarios_1_e_2():
    base, conjuntos = _conjuntos_pequenos()
    particoes = dividir_temporal(base)
    pd.testing.assert_frame_equal(conjuntos["treino"], particoes["treino"])
    pd.testing.assert_frame_equal(conjuntos["treino_total"], particoes["treino_total"])
    assert len(conjuntos["treino_c3"]) < len(conjuntos["treino"])


def test_conjuntos_naturais_e_segmentos():
    _, conjuntos = _conjuntos_pequenos()
    novos = conjuntos["locais_novos"]
    naturais = novos[novos["origem"] == "natural"].set_index("conjunto")["gmap_id"]
    assert naturais["validacao"] == "x"
    assert naturais["teste"] == "y"
    validacao = conjuntos["validacao"]
    assert validacao.loc[validacao["user_id"] == "v", "segmento"].unique().tolist() == ["novo"]
    assert validacao.loc[validacao["user_id"] == "u", "segmento"].unique().tolist() == ["antigo"]
    assert {"segmento_c3", "avaliacoes_no_treino_c3"} <= set(conjuntos["teste"].columns)


def test_conjuntos_reproduziveis():
    _, primeiro = _conjuntos_pequenos()
    _, segundo = _conjuntos_pequenos()
    pd.testing.assert_frame_equal(primeiro["locais_novos"], segundo["locais_novos"])


def _alvo_usuario_novo():
    linhas = [
        ("u1", "b", 5, "2019-05-02", "novo"),
        ("u1", "a", 4, "2019-05-01", "novo"),
        ("u1", "c", 2, "2019-06-01", "novo"),
        ("u2", "a", 5, "2019-05-01", "novo"),
        ("u3", "c", 5, "2019-05-01", "novo"),
        ("u3", "b", 3, "2019-05-01", "novo"),
        ("u4", "a", 5, "2019-05-01", "antigo"),
        ("u4", "b", 5, "2019-05-02", "antigo"),
    ]
    alvo = pd.DataFrame(linhas, columns=["user_id", "gmap_id", "rating", "data", "segmento"])
    return alvo.assign(data=pd.to_datetime(alvo["data"]))


def _locais_cadastro():
    return pd.DataFrame(
        {"gmap_id": ["a", "b", "c"], "cidade": ["X", "Y", None], "categoria_principal": ["Cafe", "Bar", "Pizza restaurant"]}
    )


def test_cadastro_simulado_e_a_primeira_avaliacao_de_quem_tem_duas_ou_mais():
    cadastros, pares = simular_cadastros(_alvo_usuario_novo(), _locais_cadastro())
    # u2 tem só uma avaliação; u4 não é novo.
    assert sorted(cadastros.index) == ["u1", "u3"]
    assert cadastros.loc["u1", "local_exemplo"] == "a"
    assert cadastros.loc["u1", "cidade"] == "X"
    assert cadastros.loc["u1", "categorias"] == ["Cafe"]
    assert sorted(map(tuple, pares.to_numpy())) == [("u1", "a"), ("u3", "b")]


def test_cadastro_simulado_desempata_a_data_pelo_local_e_aceita_local_sem_cidade():
    cadastros, _ = simular_cadastros(_alvo_usuario_novo(), _locais_cadastro())
    # u3 avaliou b e c no mesmo dia: fica b, o primeiro em ordem de gmap_id.
    assert cadastros.loc["u3", "local_exemplo"] == "b"
    alvo = _alvo_usuario_novo()
    alvo.loc[alvo["user_id"] == "u3", "gmap_id"] = ["c", "c"]
    cadastros, _ = simular_cadastros(alvo, _locais_cadastro())
    assert not isinstance(cadastros.loc["u3", "cidade"], str)
