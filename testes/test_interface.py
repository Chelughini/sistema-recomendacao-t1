import pandas as pd

from src.interface import (
    FAMILIA_PADRAO,
    NumeracaoUsuarios,
    atributos_declarados,
    cadastro_do_local,
    cartao_html,
    familia,
    historico_do_usuario,
    motivo_para_local_novo,
    opcoes_atributos,
    opcoes_categorias,
    pesos_do_perfil,
    prateleiras,
    resumo_do_perfil,
    rotulo_categorias,
)
from src.recomendador import Recomendador


def _locais():
    return pd.DataFrame(
        {
            "gmap_id": ["pizza1", "pizza2", "cafe1", "cafe2", "fechado", "novo_real", "longe"],
            "name": ["Pizza Um", "Pizza Dois", "Café Um", "Café Dois", "Fechado", "Novo", "Longe"],
            "cidade": ["X", "X", "X", "X", "X", "X", "Z"],
            "categoria_principal": ["Pizza restaurant"] * 2 + ["Cafe"] * 2 + ["Bar", "Bar", "Bar"],
            "category": [["Pizza restaurant"], ["Pizza restaurant"], ["Cafe"], ["Cafe"], ["Pizza restaurant"], ["Cafe"], ["Cafe"]],
            "MISC": [{"Amenities": ["Wi-Fi"]}] * 6 + [{"Amenities": ["Wi-Fi"], "Payments": ["Cash-only"]}],
            "latitude": [0.0] * 7,
            "longitude": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 9.0],
            "fechado_perm": [False, False, False, False, True, False, False],
            "fechado_temp": False,
        }
    )


def _treino():
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


def _modelo():
    return Recomendador(percentil=50, centro="fixo", local="cidade").ajustar(_treino(), _locais())


def test_numeracao_aceita_numero_com_ou_sem_marcas_e_o_identificador():
    numeracao = NumeracaoUsuarios(["c", "a", "b"])
    assert numeracao.buscar("1") == "a" and numeracao.buscar("#3") == "c" and numeracao.buscar(" 2 ") == "b"
    assert numeracao.buscar("b") == "b"
    assert numeracao.rotulo("c") == "Usuário #3"


def test_numeracao_rejeita_fora_do_intervalo_texto_e_vazio():
    numeracao = NumeracaoUsuarios(["a", "b"])
    assert numeracao.buscar("0") is None and numeracao.buscar("3") is None
    assert numeracao.buscar("abc") is None and numeracao.buscar("") is None and numeracao.buscar(None) is None


def test_numeracao_aceita_ponto_de_milhar():
    numeracao = NumeracaoUsuarios([f"u{i:05d}" for i in range(1500)])
    assert numeracao.buscar("1.234") == numeracao.ids[1233]
    assert numeracao.rotulo(numeracao.ids[1233]) == "Usuário #1.234"


def test_rotulos_de_categorias_traduzem_sem_repetir():
    assert rotulo_categorias(["Pizza restaurant", "Cafe", "Pizza restaurant"]) == "Pizzaria, Café"
    assert rotulo_categorias(["Categoria inexistente"]) == "Categoria inexistente"
    assert rotulo_categorias(None) == ""


def test_opcoes_so_com_o_que_o_modelo_conhece():
    modelo = _modelo()
    assert opcoes_categorias(modelo) == {"Café": "Cafe", "Pizzaria": "Pizza restaurant"}
    # "Cash-only" aparece em um local só e fica fora do vocabulário (min_df=2).
    assert opcoes_atributos(modelo) == {"Wi-Fi": ("Amenities", "Wi-Fi")}


def test_atributos_declarados_no_formato_misc():
    assert atributos_declarados([("Amenities", "Wi-Fi"), ("Payments", "Checks"), ("Amenities", "Restroom")]) == {
        "Amenities": ["Wi-Fi", "Restroom"],
        "Payments": ["Checks"],
    }
    assert atributos_declarados([]) is None


def test_perfil_resumido_e_em_grafico_com_sinais_certos():
    modelo = _modelo()
    resumo = resumo_do_perfil(modelo, "ana")
    assert resumo["gosta"][0] == "Pizzaria" and resumo["evita"] == ["Café"]
    pesos = pesos_do_perfil(modelo, "ana")
    assert set(pesos.loc[pesos["peso"] > 0, "sentido"]) == {"gosta mais"}
    assert pesos.loc[pesos["caracteristica"] == "Café", "sentido"].item() == "gosta menos"


def test_historico_ordenado_pela_nota():
    historico = historico_do_usuario(_modelo(), "ana")
    assert historico["Local"].tolist() == ["Pizza Um", "Fechado", "Café Um"]
    assert historico["Nota"].tolist() == [5, 4, 1]


def test_motivo_cita_a_cidade_do_local_ou_a_principal():
    modelo = _modelo()
    vetor = modelo.vetorizador.transform([{"category": ["Cafe"], "MISC": {}}])
    assert motivo_para_local_novo(modelo, "bia", vetor, "Z").startswith("Avaliou 1 de 4 locais em Z.")
    assert motivo_para_local_novo(modelo, "bia", vetor, "Gotham").startswith("Avalia sobretudo em X (3 de 4).")


def test_prateleiras_tiram_tudo_da_pontuacao_do_modelo():
    modelo = _modelo()
    linhas = prateleiras(modelo, "ana", n=2, minimo=1)
    titulos = [linha["titulo"] for linha in linhas]
    assert titulos[0] == "Top para você" and "Novidades para você" in titulos and titulos[-1] == "Bem avaliados perto de você"
    assert linhas[0]["tabela"]["gmap_id"].tolist() == modelo.recomendar("ana", n=2, com_explicacao=False)["gmap_id"].tolist()
    novidades = next(linha["tabela"] for linha in linhas if linha["titulo"] == "Novidades para você")
    assert set(novidades["gmap_id"]) <= set(modelo.locais_novos)
    assert all(len(linha["tabela"]) <= 2 for linha in linhas)
    avaliados = set(_treino().query("user_id == 'ana'")["gmap_id"])
    assert all(not (set(linha["tabela"]["gmap_id"]) & avaliados) for linha in linhas)


def test_familia_pela_palavra_chave():
    assert familia("Pizza delivery")[0] == "🍕"
    assert familia("Coffee shop")[0] == "☕"
    assert familia("Restaurant") == FAMILIA_PADRAO and familia(None) == FAMILIA_PADRAO


def test_cartao_escapa_html_e_marca_novo():
    linha = {"nome": "<b>Bar</b>", "cidade": "X", "categoria_principal": "Bar", "pontuacao": 0.756, "novo": True, "explicacao": "Porque <i>sim</i>."}
    html = cartao_html(linha, 1, "Bar", 4.25)
    assert "&lt;b&gt;Bar&lt;/b&gt;" in html and "<b>" not in html and "&lt;i&gt;" in html
    assert "NOVO" in html and "76% compatível · ★ 4,2" in html


def test_cadastro_do_local_no_formato_do_recomendador():
    local = _locais().iloc[6]
    cadastro = cadastro_do_local(local)
    assert cadastro["category"] == ["Cafe"] and cadastro["cidade"] == "Z" and cadastro["MISC"]["Payments"] == ["Cash-only"]
