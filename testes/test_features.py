import joblib
import numpy as np
import pandas as pd
import pytest

from src.dados import GRUPOS_DERIVADOS, GRUPOS_TEMPORARIOS
from src.features import SINONIMOS, VALORES_EXCLUIDOS, VetorizadorConteudo, tokens_do_local


def _local(categorias, **misc):
    return {"category": categorias, "MISC": {grupo.replace("_", " "): valores for grupo, valores in misc.items()}}


LOCAIS = [
    _local(["Pizza restaurant", "Bar"], Service_options=["Delivery", "Takeout"], Payments=["Credit cards"]),
    _local(["Pizza restaurant"], Service_options=["Delivery"], Amenities=["Wi-Fi"]),
    _local(["Bar", "Pub"], Service_options=["Takeout"], Amenities=["Wi-Fi"]),
    _local(["Coffee shop", "Pub"], Payments=["Credit cards"]),
]


def test_formato_dos_tokens():
    tokens = tokens_do_local(_local(["Pizza restaurant"], Service_options=["Dine-in"]))
    assert tokens["categorias"] == ["cat=pizza_restaurant"]
    assert tokens["atributos"] == ["misc=service_options:dine-in"]


@pytest.mark.parametrize("grupo", GRUPOS_DERIVADOS + GRUPOS_TEMPORARIOS)
def test_grupos_excluidos_nunca_geram_token(grupo):
    tokens = tokens_do_local({"category": ["Bar"], "MISC": {grupo: ["Qualquer valor"]}})
    assert tokens["atributos"] == []


@pytest.mark.parametrize("valor", sorted(VALORES_EXCLUIDOS))
def test_valores_excluidos_nunca_geram_token(valor):
    grupo = "Planning" if valor in {"Usually a wait", "Quick visit"} else "Service options"
    tokens = tokens_do_local({"category": ["Bar"], "MISC": {grupo: [valor]}})
    assert tokens["atributos"] == []


@pytest.mark.parametrize("original, canonico", sorted(SINONIMOS.items()))
def test_sinonimos_viram_o_mesmo_token(original, canonico):
    def tokens(valor):
        return tokens_do_local({"MISC": {"Amenities": [valor]}})["atributos"]

    assert tokens(original) == tokens(canonico)


def test_sinonimos_no_mesmo_local_nao_repetem_token():
    tokens = tokens_do_local(_local(["Bar"], Service_options=["Takeout", "Takeaway"]))
    assert tokens["atributos"] == ["misc=service_options:takeout"]


def test_tokens_aceitam_formato_do_parquet_e_ausentes():
    linha = pd.Series(
        {
            "category": np.array(["Bar"]),
            "MISC": {"Amenities": np.array(["Wi-Fi"]), "Payments": None, "Crowd": np.array(["Groups"])},
        }
    )
    assert tokens_do_local(linha) == {"categorias": ["cat=bar"], "atributos": ["misc=amenities:wi-fi"]}
    assert tokens_do_local({"category": None, "MISC": None}) == {"categorias": [], "atributos": []}
    assert tokens_do_local({"category": float("nan"), "MISC": float("nan")}) == {"categorias": [], "atributos": []}
    assert tokens_do_local({}) == {"categorias": [], "atributos": []}


def test_normas_iguais_a_um():
    matriz = VetorizadorConteudo().fit_transform(LOCAIS)
    assert np.allclose(np.sqrt(matriz.multiply(matriz).sum(axis=1)), 1)


def test_produto_escalar_e_cosseno_entre_zero_e_um():
    matriz = VetorizadorConteudo().fit_transform(LOCAIS)
    similaridades = (matriz @ matriz.T).toarray()
    assert np.allclose(np.diag(similaridades), 1)
    assert similaridades.min() >= 0
    assert similaridades[0, 1] > similaridades[0, 3]


def test_min_df_retira_token_de_um_so_local():
    vetorizador = VetorizadorConteudo().fit(LOCAIS)
    assert "cat=coffee_shop" not in vetorizador.nomes_features()
    assert "cat=pizza_restaurant" in vetorizador.nomes_features()


def test_local_novo_com_categoria_inexistente():
    vetorizador = VetorizadorConteudo().fit(LOCAIS)
    conhecido_e_novo = vetorizador.transform([_local(["Bar", "Categoria inexistente"])])
    assert conhecido_e_novo.shape[1] == len(vetorizador.nomes_features())
    assert conhecido_e_novo.nnz == 1
    assert conhecido_e_novo.sum() == pytest.approx(1)


def test_local_so_com_tokens_desconhecidos_vira_vetor_vazio():
    vazio = VetorizadorConteudo().fit(LOCAIS).transform([_local(["Categoria inexistente"])])
    assert vazio.nnz == 0


def test_transformar_nao_altera_o_vocabulario():
    vetorizador = VetorizadorConteudo().fit(LOCAIS)
    antes = vetorizador.nomes_features().tolist()
    vetorizador.transform([_local(["Categoria inexistente"])])
    assert vetorizador.nomes_features().tolist() == antes


def test_peso_zero_remove_o_bloco():
    so_categorias = VetorizadorConteudo(peso_atributos=0)
    matriz = so_categorias.fit_transform(LOCAIS)
    assert all(nome.startswith("cat=") for nome in so_categorias.nomes_features())
    assert matriz.shape[1] == len(so_categorias.nomes_features())
    assert (matriz.data != 0).all()

    so_atributos = VetorizadorConteudo(peso_categorias=0)
    so_atributos.fit(LOCAIS)
    assert all(nome.startswith("misc=") for nome in so_atributos.nomes_features())


def test_peso_muda_a_importancia_do_bloco():
    def massa_de_categorias(vetorizador):
        matriz = vetorizador.fit_transform(LOCAIS).toarray()
        eh_categoria = np.char.startswith(vetorizador.nomes_features().astype(str), "cat=")
        return (matriz[:, eh_categoria] ** 2).sum()

    assert massa_de_categorias(VetorizadorConteudo(peso_atributos=0.5)) > massa_de_categorias(VetorizadorConteudo())


def test_pesos_invalidos_geram_erro():
    with pytest.raises(ValueError):
        VetorizadorConteudo(peso_categorias=0, peso_atributos=0)
    with pytest.raises(ValueError):
        VetorizadorConteudo(peso_categorias=-1)


def test_salvar_e_carregar_reproduz_o_resultado(tmp_path):
    vetorizador = VetorizadorConteudo(peso_atributos=0.5).fit(LOCAIS)
    caminho = tmp_path / "vetorizador.joblib"
    joblib.dump(vetorizador, caminho)
    carregado = joblib.load(caminho)
    assert (vetorizador.transform(LOCAIS) != carregado.transform(LOCAIS)).nnz == 0
    assert carregado.nomes_features().tolist() == vetorizador.nomes_features().tolist()


def test_idf_fica_na_ordem_das_colunas_e_e_maior_para_token_raro():
    vetorizador = VetorizadorConteudo().fit(LOCAIS)
    idf = vetorizador.idf_por_token()
    assert idf.index.tolist() == vetorizador.nomes_features().tolist()
    assert idf["cat=pub"] == idf["cat=bar"]
    assert idf["misc=service_options:delivery"] == idf["misc=service_options:takeout"]
    assert (idf > 0).all()


def test_opcoes_de_conferencia_ficam_desligadas_por_padrao():
    local = {"category": ["Bar"], "MISC": {"Crowd": ["Groups"]}, "preco_nivel": 2.0}
    assert tokens_do_local(local)["atributos"] == []
    assert tokens_do_local(local, incluir_derivados=True)["atributos"] == ["misc=crowd:groups"]
    assert tokens_do_local(local, incluir_preco=True)["atributos"] == ["misc=preco:2"]
    assert tokens_do_local({"preco_nivel": float("nan")}, incluir_preco=True)["atributos"] == []


def test_vetorizador_repassa_as_opcoes_de_conferencia():
    locais = [
        {"category": ["Bar"], "MISC": {"Crowd": ["Groups"]}, "preco_nivel": 2.0},
        {"category": ["Bar"], "MISC": {"Crowd": ["Groups"]}, "preco_nivel": 2.0},
    ]
    nomes = VetorizadorConteudo(incluir_derivados=True, incluir_preco=True).fit(locais).nomes_features().tolist()
    assert "misc=crowd:groups" in nomes
    assert "misc=preco:2" in nomes


def test_aceita_tabela_e_lista_com_o_mesmo_resultado():
    tabela = pd.DataFrame(LOCAIS)
    vetorizador = VetorizadorConteudo().fit(LOCAIS)
    assert (vetorizador.transform(tabela) != vetorizador.transform(LOCAIS)).nnz == 0
