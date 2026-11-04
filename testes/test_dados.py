import json

import numpy as np
import pandas as pd
import pytest

from src.dados import (
    LOCAIS_INCLUIDOS_MANUALMENTE,
    atributos_do_local,
    categoria_principal,
    contar_avaliacoes_por_local,
    copias_identicas,
    eh_categoria_alimentacao,
    eh_gastronomia,
    extrair_cidade_cep,
    indice_gini,
    ler_avaliacoes,
    ler_metadados,
    limpar_avaliacoes,
    limpar_locais,
    marcar_rajadas,
    nivel_de_preco,
    no_recorte,
    tem_categoria_alimentacao,
)


def _gravar(caminho, registros):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for registro in registros:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return caminho


def _avaliacao(**campos):
    base = {
        "user_id": "115646077423418438821",
        "name": "Pessoa",
        "time": 1570739784825,
        "rating": 5,
        "text": "Ótimo café",
        "pics": None,
        "resp": None,
        "gmap_id": "a",
    }
    return {**base, **campos}


def test_metadados_mantem_todos_os_campos(tmp_path):
    caminho = _gravar(
        tmp_path / "meta.json",
        [
            {"gmap_id": "a", "name": "Café São João", "category": ["Cafe", "Bakery"], "MISC": None},
            {"gmap_id": "b", "name": "Sem categoria", "category": None, "MISC": {"Amenities": ["Wi-Fi"]}},
        ],
    )
    locais = ler_metadados(caminho)
    assert list(locais.columns) == ["gmap_id", "name", "category", "MISC"]
    assert len(locais) == 2
    assert locais.loc[0, "name"] == "Café São João"
    assert locais.loc[0, "category"] == ["Cafe", "Bakery"]
    assert locais.loc[1, "MISC"] == {"Amenities": ["Wi-Fi"]}


def test_avaliacoes_mantem_so_os_locais_selecionados(tmp_path):
    caminho = _gravar(
        tmp_path / "rev.json",
        [_avaliacao(gmap_id="a"), _avaliacao(gmap_id="b"), _avaliacao(gmap_id="c")],
    )
    avaliacoes = ler_avaliacoes(caminho, ["a", "c"])
    assert avaliacoes["gmap_id"].tolist() == ["a", "c"]


def test_avaliacoes_guarda_so_as_colunas_pedidas(tmp_path):
    caminho = _gravar(tmp_path / "rev.json", [_avaliacao()])
    avaliacoes = ler_avaliacoes(caminho, ["a"])
    assert list(avaliacoes.columns) == [
        "user_id", "gmap_id", "rating", "time", "text", "tem_foto", "tem_resposta",
    ]


def test_avaliacoes_preserva_valores_e_identificador_longo(tmp_path):
    caminho = _gravar(tmp_path / "rev.json", [_avaliacao()])
    avaliacao = ler_avaliacoes(caminho, ["a"]).iloc[0]
    assert avaliacao["user_id"] == "115646077423418438821"
    assert avaliacao["rating"] == 5
    assert avaliacao["time"] == 1570739784825
    assert avaliacao["text"] == "Ótimo café"


def test_indicadores_de_foto_e_resposta(tmp_path):
    caminho = _gravar(
        tmp_path / "rev.json",
        [
            _avaliacao(),
            _avaliacao(pics=[{"url": ["x"]}], resp={"time": 1, "text": "Obrigado"}),
            _avaliacao(pics=[]),
        ],
    )
    avaliacoes = ler_avaliacoes(caminho, ["a"])
    assert avaliacoes["tem_foto"].tolist() == [False, True, False]
    assert avaliacoes["tem_resposta"].tolist() == [False, True, False]


def test_avaliacao_sem_nota_e_sem_texto_continua_na_leitura(tmp_path):
    caminho = _gravar(
        tmp_path / "rev.json",
        [_avaliacao(user_id=None, rating=None, text=None), _avaliacao()],
    )
    avaliacoes = ler_avaliacoes(caminho, ["a"])
    assert len(avaliacoes) == 2
    assert pd.isna(avaliacoes.loc[0, "user_id"])
    assert pd.isna(avaliacoes.loc[0, "rating"])
    assert pd.isna(avaliacoes.loc[0, "text"])


def test_nenhum_local_selecionado_devolve_tabela_vazia(tmp_path):
    caminho = _gravar(tmp_path / "rev.json", [_avaliacao()])
    avaliacoes = ler_avaliacoes(caminho, [])
    assert avaliacoes.empty
    assert "rating" in avaliacoes.columns


def test_contagem_de_avaliacoes_por_local(tmp_path):
    caminho = _gravar(
        tmp_path / "rev.json",
        [_avaliacao(gmap_id="a"), _avaliacao(gmap_id="a"), _avaliacao(gmap_id="b")],
    )
    assert contar_avaliacoes_por_local(caminho) == {"a": 2, "b": 1}


@pytest.mark.parametrize(
    "categorias, esperado",
    [
        (["Caterer", "Restaurant"], True),
        (["Hotel", "Restaurant"], False),
        (["Restaurant", "Hotel"], True),
        (["Caterer"], False),
        (["Barber shop"], False),
        (["Public library"], False),
        (["Delivery service"], False),
        (["Seafood market"], False),
        (["Bar"], True),
        (["Bar & grill"], True),
        (["Pub"], True),
        (["Gastropub"], True),
        (["Deli"], True),
        (["Hamburger restaurant"], True),
        (["Cafeteria"], True),
        (["Bar stool supplier"], False),
        (["Internet cafe"], False),
        (["Bed & breakfast", "Restaurant"], False),
        (np.array(["Pizza restaurant", "Hotel"]), True),
        ([], False),
        (None, False),
        (float("nan"), False),
    ],
)
def test_recorte_pela_categoria_principal(categorias, esperado):
    assert eh_gastronomia(categorias) is esperado


def test_categoria_principal_ignora_so_caterer():
    assert categoria_principal(["Caterer", "Bakery", "Cafe"]) == "Bakery"
    assert categoria_principal(["Hotel", "Caterer"]) == "Hotel"
    assert categoria_principal(["Caterer"]) is None
    assert categoria_principal(None) is None


def test_exclusao_nao_depende_de_maiusculas():
    assert not eh_categoria_alimentacao("HOOKAH BAR")
    assert eh_categoria_alimentacao("  sports bar ")


def test_alguma_categoria_de_comida_olha_a_lista_inteira():
    assert tem_categoria_alimentacao(["Hotel", "Restaurant"])
    assert not tem_categoria_alimentacao(["Hotel", "Spa"])
    assert not tem_categoria_alimentacao(None)


def test_no_recorte_soma_regra_e_inclusao_manual():
    incluido = next(iter(LOCAIS_INCLUIDOS_MANUALMENTE))
    locais = pd.DataFrame(
        {
            "gmap_id": ["a", "b", incluido, "c"],
            "category": [["Restaurant"], ["Hotel", "Restaurant"], ["Dinner theater"], None],
        }
    )
    assert no_recorte(locais).tolist() == [True, False, True, False]


def _local(**campos):
    base = {
        "gmap_id": "a",
        "name": "Local",
        "address": "Local, 1 Main St, Lander, WY 82520",
        "latitude": 42.8,
        "longitude": -108.7,
        "category": ["Restaurant"],
        "avg_rating": 4.5,
        "num_of_reviews": 10,
        "price": "$$",
        "hours": None,
        "MISC": None,
        "state": "Open now",
        "url": "http://exemplo",
    }
    return {**base, **campos}


def _bruta(**campos):
    base = {
        "user_id": "u1",
        "gmap_id": "a",
        "rating": 5.0,
        "time": 1570739784825,
        "text": "Bom",
        "tem_foto": False,
        "tem_resposta": False,
    }
    return {**base, **campos}


@pytest.mark.parametrize(
    "endereco, esperado",
    [
        ("Local, 1 Main St, Lander, WY 82520", ("Lander", "82520")),
        ("Local, 1 Main St, Rock Springs, WY 82901, United States", ("Rock Springs", "82901")),
        ("Savageton Bar, Wyoming 82718", (None, "82718")),
        ("Local sem nada", (None, None)),
        (None, (None, None)),
        (float("nan"), (None, None)),
    ],
)
def test_extrair_cidade_e_cep(endereco, esperado):
    assert extrair_cidade_cep(endereco) == esperado


def test_nivel_de_preco_conta_os_dois_simbolos():
    assert nivel_de_preco("$$") == 2
    assert nivel_de_preco("₩") == 1
    assert nivel_de_preco("₩₩") == 2
    assert np.isnan(nivel_de_preco(None))
    assert np.isnan(nivel_de_preco(float("nan")))


def test_copias_identicas_detecta_diferenca():
    iguais = pd.DataFrame([_local(), _local(), _local(gmap_id="b")])
    diferentes = pd.DataFrame([_local(), _local(name="Outro nome")])
    assert copias_identicas(iguais)
    assert not copias_identicas(diferentes)


def test_limpar_locais_mantem_uma_copia_e_recusa_copias_diferentes():
    assert len(limpar_locais(pd.DataFrame([_local(), _local()]))) == 1
    with pytest.raises(ValueError):
        limpar_locais(pd.DataFrame([_local(), _local(name="Outro nome")]))


def test_limpar_locais_anula_coordenada_fora_de_wyoming():
    limpos = limpar_locais(pd.DataFrame([_local(latitude=28.6, longitude=-81.0), _local(gmap_id="b")]))
    assert limpos[["latitude", "longitude"]].iloc[0].isna().all()
    assert limpos.loc[1, "latitude"] == 42.8


def test_limpar_locais_le_fechados_so_pelo_texto_do_estado():
    limpos = limpar_locais(
        pd.DataFrame(
            [
                _local(gmap_id="a", state="Permanently closed"),
                _local(gmap_id="b", state="Temporarily closed"),
                _local(gmap_id="c", state="Closed ⋅ Opens 7AM"),
                _local(gmap_id="d", state=None),
            ]
        )
    )
    assert limpos["fechado_perm"].tolist() == [True, False, False, False]
    assert limpos["fechado_temp"].tolist() == [False, True, False, False]


def test_limpar_locais_ajusta_colunas():
    limpos = limpar_locais(pd.DataFrame([_local(category=["Caterer", "Bakery"], price="₩")]))
    assert not {"url", "hours", "avg_rating", "num_of_reviews"} & set(limpos.columns)
    assert limpos.loc[0, "avg_rating_google"] == 4.5
    assert limpos.loc[0, "num_of_reviews_google"] == 10
    assert limpos.loc[0, "categoria_principal"] == "Bakery"
    assert limpos.loc[0, "cidade"] == "Lander"
    assert limpos.loc[0, "cep"] == "82520"
    assert limpos.loc[0, "preco_nivel"] == 1


def test_limpar_avaliacoes_remove_sem_nota_e_sem_usuario():
    limpas, funil = limpar_avaliacoes(
        pd.DataFrame([_bruta(), _bruta(rating=None, user_id=None), _bruta(user_id=None, gmap_id="b")])
    )
    assert len(limpas) == 1
    assert funil.loc[1, "removidas"] == 2


def test_limpar_avaliacoes_remove_duplicata_exata_mesmo_sem_texto():
    limpas, funil = limpar_avaliacoes(pd.DataFrame([_bruta(text=None), _bruta(text=None), _bruta(gmap_id="b")]))
    assert len(limpas) == 2
    assert funil.loc[2, "removidas"] == 1
    assert funil.loc[3, "removidas"] == 0


def test_limpar_avaliacoes_mantem_a_mais_recente_do_mesmo_usuario_e_local():
    limpas, funil = limpar_avaliacoes(
        pd.DataFrame([_bruta(time=1000, rating=1.0), _bruta(time=2000, rating=5.0), _bruta(user_id="u2")])
    )
    assert len(limpas) == 2
    assert limpas.loc[limpas["user_id"] == "u1", "rating"].item() == 5
    assert funil.loc[3, "removidas"] == 1


def test_limpar_avaliacoes_recusa_nota_fora_da_faixa():
    for nota in [0.0, 6.0, 4.5]:
        with pytest.raises(ValueError):
            limpar_avaliacoes(pd.DataFrame([_bruta(rating=nota)]))


def test_limpar_avaliacoes_cria_datas_e_indicador_de_texto():
    limpas, _ = limpar_avaliacoes(pd.DataFrame([_bruta(), _bruta(user_id="u2", text=None)]))
    assert "time" not in limpas.columns
    assert limpas.loc[0, "data"] == pd.Timestamp("2019-10-10 20:36:24.825")
    assert limpas.loc[0, "ano"] == 2019
    assert limpas.loc[0, "mes"] == 10
    assert limpas["tem_texto"].tolist() == [True, False]
    assert limpas["rating"].dtype == "int64"


def test_marcar_rajadas_exige_cinco_no_mesmo_minuto_do_mesmo_usuario():
    base = pd.Timestamp("2020-01-01 10:00:00")
    linhas = [{"user_id": "u1", "gmap_id": str(i), "data": base + pd.Timedelta(seconds=i)} for i in range(5)]
    linhas += [{"user_id": "u2", "gmap_id": str(i), "data": base + pd.Timedelta(minutes=i)} for i in range(5)]
    linhas += [{"user_id": "u3", "gmap_id": str(i), "data": base} for i in range(4)]
    assert marcar_rajadas(pd.DataFrame(linhas)).tolist() == [True] * 5 + [False] * 9


def test_indice_gini_com_resultados_conhecidos():
    assert indice_gini([5, 5, 5, 5]) == pytest.approx(0)
    assert indice_gini([0, 0, 0, 10]) == pytest.approx(0.75)
    assert indice_gini([3, 1, 2]) == pytest.approx(2 / 9)


def test_atributos_do_local_aceita_ausentes_e_arrays():
    misc = {"Amenities": ["Wi-Fi", "Bar"], "Payments": None, "Planning": np.array(["Reservas"])}
    assert atributos_do_local(misc) == ["Amenities: Wi-Fi", "Amenities: Bar", "Planning: Reservas"]
    assert atributos_do_local(None) == []
    assert atributos_do_local(float("nan")) == []
