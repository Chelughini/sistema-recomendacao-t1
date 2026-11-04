import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from src.metricas import (
    auc,
    avaliar,
    comparar,
    correlacao_rankings,
    curva_roc,
    curva_roc_media,
    erros_de_nota,
    intervalo,
    montar_protocolo,
)


def test_auc_com_resultados_conhecidos():
    assert auc([3, 4], [1, 2]) == 1
    assert auc([1, 2], [3, 4]) == 0
    assert auc([1, 3], [2]) == 0.5


def test_auc_com_empate_vale_meio():
    assert auc([1], [1]) == 0.5
    assert auc([2, 1], [1]) == 0.75


def test_auc_sem_um_dos_grupos_e_nan():
    assert np.isnan(auc([], [1]))
    assert np.isnan(auc([1], []))


def test_curva_roc_com_resultado_conhecido():
    falsos, verdadeiros = curva_roc([1, 0, 1, 0], [4, 3, 2, 1])
    assert falsos.tolist() == [0, 0, 0.5, 0.5, 1]
    assert verdadeiros.tolist() == [0, 0.5, 0.5, 1, 1]


def test_curva_roc_agrupa_empates_na_diagonal():
    falsos, verdadeiros = curva_roc([1, 0], [1, 1])
    assert falsos.tolist() == [0, 1]
    assert verdadeiros.tolist() == [0, 1]


def test_area_da_curva_roc_coincide_com_auc():
    rotulos = np.array([1, 0, 1, 0, 0, 1], dtype=bool)
    valores = np.array([5, 4, 4, 2, 1, 3], dtype=float)
    falsos, verdadeiros = curva_roc(rotulos, valores)
    assert np.trapezoid(verdadeiros, falsos) == pytest.approx(auc(valores[rotulos], valores[~rotulos]))


def test_curva_roc_media_entre_usuarios():
    grade, media = curva_roc_media([([1, 0], [2, 1]), ([1, 0], [1, 2])], pontos=3)
    assert grade.tolist() == [0, 0.5, 1]
    assert media[1] == pytest.approx(0.5)
    assert media[-1] == 1


def test_correlacao_com_resultado_conhecido():
    spearman, kendall = correlacao_rankings([1, 2, 3], [1, 2, 3])
    assert spearman == pytest.approx(1)
    assert kendall == pytest.approx(1)
    spearman, kendall = correlacao_rankings([3, 2, 1], [1, 2, 3])
    assert spearman == pytest.approx(-1)
    assert kendall == pytest.approx(-1)


def test_correlacao_sem_variacao_nao_quebra():
    assert np.isnan(correlacao_rankings([1, 2, 3], [4, 4, 4])[0])
    assert np.isnan(correlacao_rankings([2, 2, 2], [1, 2, 3])[1])
    assert np.isnan(correlacao_rankings([1, 2], [1, 2])[0])


def test_erros_de_nota_com_resultado_conhecido():
    resultado = erros_de_nota([1, 3, 5], [2, 3, 3])
    assert resultado["MAE"] == pytest.approx(1)
    assert resultado["MSE"] == pytest.approx(5 / 3)
    assert resultado["RMSE"] == pytest.approx(np.sqrt(5 / 3))


def _locais():
    nomes = ["a", "b", "c", "d", "fechado", "temporario", "sem_treino"]
    return pd.DataFrame(
        {
            "gmap_id": nomes,
            "fechado_perm": [nome == "fechado" for nome in nomes],
            "fechado_temp": [nome == "temporario" for nome in nomes],
        }
    )


def _treino():
    pares = [("u1", "a"), ("u1", "fechado"), ("u1", "temporario"), ("u2", "b"), ("u3", "a"), ("u4", "c"), ("u5", "d")]
    return pd.DataFrame(pares, columns=["user_id", "gmap_id"])


def _alvo():
    linhas = [
        ("u1", "b", 5, "antigo"),
        ("u1", "c", 2, "antigo"),
        ("u1", "fechado", 5, "antigo"),
        ("u1", "sem_treino", 5, "antigo"),
        ("u2", "a", 4, "antigo"),
        ("u3", "b", 3, "antigo"),
        ("u4", "a", 5, "novo"),
        ("u5", "fechado", 5, "antigo"),
    ]
    return pd.DataFrame(linhas, columns=["user_id", "gmap_id", "rating", "segmento"])


def _protocolo(**opcoes):
    return montar_protocolo(_treino(), _alvo(), _locais(), ["antigo"], **opcoes)


def test_protocolo_exclui_fechados_e_locais_fora_do_treino():
    assert _protocolo().candidatos.tolist() == ["a", "b", "c", "d"]


def test_protocolo_so_tem_usuarios_do_segmento_com_conversao_entre_candidatos():
    # u3 só tem nota 3, u4 é de outro segmento e u5 só converteu em local fechado.
    assert _protocolo().usuarios.tolist() == ["u1", "u2"]


def test_protocolo_aceita_varios_segmentos_e_lista_de_candidatos():
    varios = montar_protocolo(_treino(), _alvo(), _locais(), ["antigo", "novo"])
    assert varios.usuarios.tolist() == ["u1", "u2", "u4"]
    informados = montar_protocolo(_treino(), _alvo(), _locais(), ["antigo"], candidatos=["sem_treino", "b"])
    assert informados.candidatos.tolist() == ["b", "sem_treino"]
    assert informados.usuarios.tolist() == ["u1"]


def test_protocolo_sorteia_usuarios_quando_passa_do_maximo():
    primeiro = _protocolo(maximo_usuarios=1)
    assert len(primeiro.usuarios) == 1
    assert primeiro.usuarios.tolist() == _protocolo(maximo_usuarios=1).usuarios.tolist()


def test_protocolo_guarda_notas_e_avaliados_do_treino():
    protocolo = _protocolo()
    assert protocolo.notas.toarray().tolist() == [[0, 5, 2, 0], [4, 0, 0, 0]]
    assert protocolo.ja_avaliados.toarray().tolist() == [[1, 0, 0, 0], [0, 1, 0, 0]]
    assert protocolo.contagem_treino.tolist() == [2, 1, 1, 1]
    assert protocolo.total_treino == 7


def test_pares_excluidos_saem_do_alvo_e_da_lista():
    excluidos = pd.DataFrame({"user_id": ["u1"], "gmap_id": ["c"]})
    protocolo = _protocolo(pares_excluidos=excluidos)
    assert protocolo.notas.toarray()[0].tolist() == [0, 5, 0, 0]
    assert protocolo.ja_avaliados.toarray()[0].tolist() == [1, 0, 1, 0]


def _modelo_fixo(matriz):
    return lambda usuarios, candidatos: np.array(matriz, dtype=float)


def test_avaliados_no_treino_saem_da_lista_e_conversao_usa_o_tamanho_real():
    # u1 já avaliou a; a lista dele tem b e c. u2 já avaliou b; a lista dele tem a e d.
    resultado = avaliar(_protocolo(), _modelo_fixo([[9, 8, 7, 1], [9, 8, 1, 7]]), k=2)
    candidatos = _protocolo().candidatos
    assert candidatos[resultado.listas[0]].tolist() == ["b", "c"]
    assert candidatos[resultado.listas[1]].tolist() == ["a", "d"]
    # u1: b converte e c tem nota 2. u2: a converte.
    assert resultado.por_usuario["conversao"].tolist() == [0.5, 0.5]
    assert resultado.por_usuario.loc["u1", "consumo"] == 1


def test_auc_de_gosto_so_para_usuario_com_os_dois_tipos():
    resultado = avaliar(_protocolo(), _modelo_fixo([[0, 2, 1, 0], [1, 0, 0, 0]]), k=2)
    assert resultado.por_usuario.loc["u1", "auc_gosto"] == 1
    assert np.isnan(resultado.por_usuario.loc["u2", "auc_gosto"])
    invertido = avaliar(_protocolo(), _modelo_fixo([[0, 1, 2, 0], [1, 0, 0, 0]]), k=2)
    assert invertido.por_usuario.loc["u1", "auc_gosto"] == 0


def test_auc_de_consumo_compara_convertidos_com_demais_candidatos():
    resultado = avaliar(_protocolo(), _modelo_fixo([[9, 3, 2, 1], [3, 9, 2, 1]]), completo=True)
    # u1: b (positivo) acima de c e d. u2: a (positivo) acima de c e d; b é excluído por estar no treino.
    assert resultado.por_usuario["auc_consumo"].tolist() == [1, 1]


def test_empates_sao_desfeitos_por_sorteio_com_semente_fixa():
    n_candidatos = 200
    protocolo = montar_protocolo(
        pd.DataFrame({"user_id": ["x"], "gmap_id": ["0"]}),
        pd.DataFrame({"user_id": ["x"], "gmap_id": [str(n_candidatos - 1)], "rating": [5], "segmento": ["antigo"]}),
        pd.DataFrame({"gmap_id": [str(i) for i in range(n_candidatos)], "fechado_perm": False, "fechado_temp": False}),
        ["antigo"],
        candidatos=[str(i) for i in range(n_candidatos)],
    )
    constante = lambda usuarios, candidatos: np.zeros((len(usuarios), len(candidatos)))
    primeira = avaliar(protocolo, constante, k=10).listas
    segunda = avaliar(protocolo, constante, k=10).listas
    assert primeira.tolist() == segunda.tolist()
    # A ordem do catálogo começaria nas posições 1 a 10.
    assert sorted(primeira[0].tolist()) != list(range(1, 11))
    assert not set(avaliar(protocolo, constante, k=10, semente=7).listas[0].tolist()) == set(primeira[0].tolist())


def test_lista_nao_inclui_par_nao_pontuavel():
    matriz = [[0, np.nan, 1, np.nan], [1, 0, np.nan, np.nan]]
    resultado = avaliar(_protocolo(), _modelo_fixo(matriz), k=3)
    candidatos = _protocolo().candidatos
    assert candidatos[resultado.listas[0][resultado.listas[0] >= 0]].tolist() == ["c"]
    assert candidatos[resultado.listas[1][resultado.listas[1] >= 0]].tolist() == ["a"]
    assert resultado.por_usuario.loc["u2", "conversao"] == 1


def test_coberturas_com_resultado_conhecido():
    resultado = avaliar(_protocolo(), _modelo_fixo([[0, 3, 2, 1], [3, 0, 2, 1]]), k=1)
    assert resultado.cobertura_catalogo == 0.5
    assert resultado.cobertura_usuarios == 0
    assert resultado.cobertura_itens == 0


def test_coberturas_de_usuarios_e_itens_contam_dez_pontuaveis():
    candidatos = [str(i) for i in range(12)]
    usuarios = [f"u{i}" for i in range(11)]
    protocolo = montar_protocolo(
        pd.DataFrame({"user_id": ["z"], "gmap_id": ["0"]}),
        pd.DataFrame({"user_id": usuarios, "gmap_id": "0", "rating": 5, "segmento": "antigo"}),
        pd.DataFrame({"gmap_id": candidatos, "fechado_perm": False, "fechado_temp": False}),
        ["antigo"],
        candidatos=candidatos,
    )
    matriz = np.ones((11, 12))
    matriz[0, :3] = np.nan  # Primeiro usuário: 9 pontuáveis, abaixo de 10.
    matriz[:, 11] = np.nan  # Último candidato: nenhum usuário.
    resultado = avaliar(protocolo, _modelo_fixo(matriz))
    assert resultado.cobertura_usuarios == pytest.approx(10 / 11)
    assert resultado.cobertura_itens == pytest.approx(11 / 12)


def test_novidade_com_resultado_conhecido():
    # Contagens: a=2, b=1, c=1, d=1 em 7 avaliações. A lista de u1 tem b e c.
    resultado = avaliar(_protocolo(), _modelo_fixo([[0, 3, 2, 1], [3, 0, 2, 1]]), k=2, completo=True)
    assert resultado.por_usuario.loc["u1", "novidade"] == pytest.approx(-np.log2(1 / 7))
    # A lista de u2 tem a e c.
    assert resultado.por_usuario.loc["u2", "novidade"] == pytest.approx((-np.log2(2 / 7) - np.log2(1 / 7)) / 2)


def test_novidade_de_local_sem_avaliacao_nao_quebra():
    protocolo = _protocolo(candidatos=["b", "sem_treino"])
    resultado = avaliar(protocolo, lambda usuarios, candidatos: np.array([[1.0, 2.0]]), k=1, completo=True)
    assert np.isfinite(resultado.por_usuario["novidade"]).all()


def test_diversidade_com_resultado_conhecido():
    vetores = sparse.csr_matrix(np.array([[1, 0], [1, 0], [0, 1], [0, 1]], dtype=float))
    # u1: b e c têm cosseno 0. u2: a e d têm cosseno 0.
    resultado = avaliar(_protocolo(), _modelo_fixo([[0, 3, 2, 1], [3, 0, 1, 2]]), k=2, completo=True, vetores=vetores)
    assert resultado.por_usuario["diversidade"].tolist() == [1, 1]
    iguais = sparse.csr_matrix(np.ones((4, 1)))
    resultado = avaliar(_protocolo(), _modelo_fixo([[0, 3, 2, 1], [3, 0, 1, 2]]), k=2, completo=True, vetores=iguais)
    assert resultado.por_usuario["diversidade"].tolist() == [0, 0]


def test_serendipidade_conta_o_que_converte_fora_da_lista_obvia():
    obvio = _modelo_fixo([[0, 3, 2, 1], [0, 0, 2, 1]])  # Óbvias: u1 = b; u2 = c.
    modelo = _modelo_fixo([[0, 3, 2, 1], [3, 0, 2, 1]])  # Lista com k=1: u1 = b; u2 = a.
    resultado = avaliar(_protocolo(), modelo, k=1, completo=True, modelo_obvio=obvio)
    assert resultado.por_usuario["serendipidade"].tolist() == [0, 1]


def test_correlacao_e_opcional_no_avaliar():
    sem = avaliar(_protocolo(), _modelo_fixo([[0, 3, 2, 1], [3, 0, 2, 1]]))
    assert "spearman" not in sem.por_usuario
    com = avaliar(_protocolo(), _modelo_fixo([[0, 3, 2, 1], [3, 0, 2, 1]]), com_correlacao=True)
    assert {"spearman", "kendall"} <= set(com.por_usuario)


def test_modelo_com_formato_errado_gera_erro():
    with pytest.raises(ValueError):
        avaliar(_protocolo(), _modelo_fixo([[1, 2]]))


def test_resumo_traz_medias_e_coberturas():
    resultado = avaliar(_protocolo(), _modelo_fixo([[9, 8, 7, 1], [9, 8, 1, 7]]), k=2)
    resumo = resultado.resumo()
    assert resumo["conversao"] == 0.5
    assert resumo["cobertura_catalogo"] == resultado.cobertura_catalogo


def test_intervalo_e_comparacao_pareada():
    protocolo = _protocolo()
    bom = avaliar(protocolo, _modelo_fixo([[0, 3, 2, 1], [3, 0, 2, 1]]), k=1)
    ruim = avaliar(protocolo, _modelo_fixo([[0, 1, 2, 3], [1, 0, 2, 3]]), k=1)
    media, inferior, superior = intervalo(bom, "conversao")
    assert media == 1 and inferior == 1 and superior == 1
    comparacao = comparar(bom, ruim, "conversao")
    assert comparacao["diferenca"] == 1
    assert comparacao["empate"] is False
    assert comparacao["usuarios"] == 2
    assert comparar(bom, bom, "conversao")["empate"] is True
