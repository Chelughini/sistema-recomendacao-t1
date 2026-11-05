"""Interface do recomendador de gastronomia em Wyoming: os três cenários do trabalho.

Rodar a partir da raiz do projeto, depois dos notebooks 01 a 03:

    streamlit run app.py
"""

import json
from pathlib import Path

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src.graficos import numero_br
from src.tema_apresentacao import CORES
from src.interface import (
    ESTILO_PRATELEIRA,
    cartao_html,
    pesos_do_perfil,
    prateleiras,
    NIVEIS_DE_PRECO,
    NumeracaoUsuarios,
    atributos_declarados,
    cadastro_do_local,
    cidades_do_usuario,
    historico_do_usuario,
    motivo_para_local_novo,
    opcoes_atributos,
    opcoes_categorias,
    resumo_do_perfil,
    rotulo_categorias,
)

RAIZ = Path(__file__).resolve().parent
PASTA_MODELOS = RAIZ / "modelos"
PASTA_CONJUNTOS = RAIZ / "data" / "processed" / "conjuntos"
NAO_INFORMAR = "(não informar)"
COMPONENTES = {"conteudo": "Conteúdo", "escore": "Escore", "local": "Localização", "popularidade": "Popularidade"}

st.set_page_config(page_title="Gastronomia em Wyoming", layout="wide")


@st.cache_resource(show_spinner="Carregando os modelos (cerca de 30 segundos na primeira vez)…")
def carregar():
    modelo = joblib.load(PASTA_MODELOS / "recomendador.joblib")
    modelo_c3 = joblib.load(PASTA_MODELOS / "recomendador_c3.joblib")
    configuracao = json.loads((PASTA_MODELOS / "configuracao.json").read_text(encoding="utf-8"))
    novos = pd.read_parquet(PASTA_CONJUNTOS / "locais_novos.parquet")
    origem = novos[novos["conjunto"] == "teste"].set_index("gmap_id")["origem"]
    locais = modelo.locais.set_index("gmap_id")
    abertos_avaliados = locais.loc[modelo.candidatos_padrao]
    return {
        "modelo": modelo,
        "modelo_c3": modelo_c3,
        "configuracao": configuracao,
        "numeracao": NumeracaoUsuarios(modelo._linha_perfil.index),
        "locais": locais,
        "origem_novos": origem,
        "cidades": sorted(abertos_avaliados["cidade"].dropna().unique()),
        "exemplos": dict(
            sorted(
                ((f"{nome} — {cidade}" if isinstance(cidade, str) else nome), gmap_id)
                for gmap_id, nome, cidade in zip(abertos_avaliados.index, abertos_avaliados["name"], abertos_avaliados["cidade"])
            )
        ),
        "categorias": opcoes_categorias(modelo),
        "atributos": opcoes_atributos(modelo),
    }


def tabela_de_locais(lista, locais, modelo=None, usuario=None):
    """Lista de locais com as barras dos componentes (0 a 100) e, se houver, a explicação."""
    tabela = pd.DataFrame(
        {
            "Posição": np.arange(1, len(lista) + 1),
            "Local": lista["nome"].to_numpy(),
            "Cidade": lista["cidade"].fillna("sem cidade").to_numpy(),
            "Categorias": [rotulo_categorias(locais.at[gmap_id, "category"]) for gmap_id in lista["gmap_id"]],
            "Pontuação": [numero_br(100 * valor, 1) for valor in lista["pontuacao"]],
        }
    )
    if "novo" in lista:
        tabela.insert(2, "Novo", lista["novo"].to_numpy())
    if modelo is not None:
        previstas = modelo.prever_nota([usuario] * len(lista), lista["gmap_id"].tolist())
        tabela["Nota prevista"] = [numero_br(valor, 1) for valor in previstas]
    for coluna, rotulo in COMPONENTES.items():
        tabela[rotulo] = (100 * lista[coluna].to_numpy()).round()
    if "explicacao" in lista:
        tabela["Por quê"] = lista["explicacao"].to_numpy()
    return tabela


def mostrar(tabela):
    configuracao = {
        rotulo: st.column_config.ProgressColumn(rotulo, min_value=0, max_value=100, format="%d", width=105)
        for rotulo in COMPONENTES.values()
    }
    configuracao["Posição"] = st.column_config.NumberColumn("Posição", width=60)
    configuracao["Local"] = st.column_config.TextColumn("Local", width=190)
    configuracao["Categorias"] = st.column_config.TextColumn("Categorias", width=200)
    configuracao["Por quê"] = st.column_config.TextColumn("Por quê", width=520)
    configuracao["Novo"] = st.column_config.CheckboxColumn("Novo", help="Local sem avaliações, que entra pela cota.")
    st.dataframe(tabela, hide_index=True, width="stretch", column_config=configuracao)


def pesos_em_texto(pesos):
    return " · ".join(f"{rotulo} {numero_br(pesos[chave], 3).rstrip('0').rstrip(',')}" for chave, rotulo in zip(["alfa", "beta", "gama", "delta"], COMPONENTES.values()))


def aviso(texto):
    """Quadro de informação com borda neutra; o st.info do Streamlit é sempre azul, fora do tema."""
    with st.container(border=True):
        st.markdown(texto)


recursos = carregar()
modelo, modelo_c3, numeracao, locais = recursos["modelo"], recursos["modelo_c3"], recursos["numeracao"], recursos["locais"]
configuracao = recursos["configuracao"]

with st.sidebar:
    st.title("Gastronomia em Wyoming")
    st.write(
        "Recomendação de restaurantes, cafés e bares com a técnica de **conteúdo e escores de produto**, "
        "sobre as avaliações do Google Local (McAuley Lab, UCSD) até 2021."
    )
    st.write(
        "A pontuação de cada local combina quatro componentes, de 0 a 100: **conteúdo** (o quanto as "
        "categorias e os atributos lembram os locais de que a pessoa gostou), **escore** (a nota média "
        "do local, com média bayesiana), **localização** (proximidade dos lugares que a pessoa avalia) e "
        "**popularidade** (quantidade de avaliações)."
    )
    n = st.slider("Tamanho da lista", min_value=5, max_value=20, value=10)
    st.caption(
        f"Modelo ajustado com {numero_br(len(modelo.treino))} avaliações de {numero_br(len(numeracao))} usuários "
        f"e {numero_br(len(locais))} locais. Os usuários aparecem só por número."
    )

aba_demo, aba_antigo, aba_novo, aba_local = st.tabs(["Demonstração", "Usuário antigo", "Usuário novo", "Local novo"])

# ---------------------------------------------------------------- Demonstração
TERRACOTA, SALVIA = CORES["terracota"], CORES["salvia"]  # tema da apresentação

with aba_demo:
    st.subheader("Demonstração: o gosto de um usuário e o que o sistema recomenda")

    def sortear_demo():
        frequentes = modelo.avaliacoes_por_usuario.index[modelo.avaliacoes_por_usuario >= 10]
        st.session_state["busca_demo"] = str(numeracao.numero(np.random.default_rng().choice(frequentes.to_numpy())))

    if "busca_demo" not in st.session_state:
        sortear_demo()
    coluna_busca, coluna_botao = st.columns([3, 1], vertical_alignment="bottom")
    texto_demo = coluna_busca.text_input("Número do usuário", key="busca_demo", placeholder=f"de 1 a {numero_br(len(numeracao))}")
    coluna_botao.button("Sortear outro", on_click=sortear_demo, help="Sorteia um usuário com 10 ou mais avaliações.", width="stretch", key="sortear_demo")
    usuario_demo = numeracao.buscar(texto_demo)

    if usuario_demo is None:
        st.error(f"Usuário não encontrado: os números vão de 1 a {numero_br(len(numeracao))}.")
    else:
        historico = historico_do_usuario(modelo, usuario_demo)
        cidades = cidades_do_usuario(modelo, usuario_demo)
        bons = int((historico["Nota"] >= 4).sum())
        st.markdown(f"## {numeracao.rotulo(usuario_demo)}")
        colunas = st.columns(4)
        colunas[0].metric("Avaliações", numero_br(len(historico)))
        colunas[1].metric("Nota média", numero_br(historico["Nota"].mean(), 1))
        colunas[2].metric("Notas 4 ou 5", f"{numero_br(100 * bons / len(historico))}%")
        colunas[3].metric("Cidade principal", cidades.index[0])

        grafico_perfil, grafico_notas = st.columns([3, 2])
        with grafico_perfil:
            st.markdown("**O que pesa no gosto**")
            pesos = pesos_do_perfil(modelo, usuario_demo)
            if len(pesos):
                barras = (
                    alt.Chart(pesos)
                    .mark_bar(cornerRadiusEnd=4, height=14)
                    .encode(
                        x=alt.X("peso:Q", title="peso no perfil (direita: gosta mais; esquerda: gosta menos)", axis=alt.Axis(labels=False, ticks=False, grid=False)),
                        y=alt.Y("caracteristica:N", sort=alt.SortField("peso", order="descending"), title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False, labelFontSize=12)),
                        color=alt.Color("sentido:N", scale=alt.Scale(domain=["gosta mais", "gosta menos"], range=[TERRACOTA, SALVIA]), legend=alt.Legend(title=None, orient="bottom")),
                        tooltip=[alt.Tooltip("caracteristica:N", title="Característica"), alt.Tooltip("sentido:N", title="Sentido")],
                    )
                    .properties(height=max(180, 30 * len(pesos)))
                )
                regua = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="gray", opacity=0.5).encode(x="x:Q")
                st.altair_chart(barras + regua, width="stretch")
            else:
                aviso("O perfil é neutro: as notas não diferenciam um tipo de local de outro.")
        with grafico_notas:
            st.markdown("**Notas que deu**")
            contagem = historico["Nota"].value_counts().reindex(range(1, 6), fill_value=0).rename_axis("nota").reset_index(name="avaliações")
            contagem["nota"] = contagem["nota"].map(lambda nota: "★" * nota)
            notas = (
                alt.Chart(contagem)
                .mark_bar(cornerRadiusEnd=4, color=TERRACOTA, height=18)
                .encode(
                    y=alt.Y("nota:N", sort=["★" * nota for nota in range(5, 0, -1)], title=None),
                    x=alt.X("avaliações:Q", title="avaliações", axis=alt.Axis(tickMinStep=1, format="d")),
                    tooltip=["nota", "avaliações"],
                )
                .properties(height=190)
            )
            st.altair_chart(notas, width="stretch")

        linhas_demo = prateleiras(modelo, usuario_demo, n=n)
        topo = linhas_demo[0]["tabela"]
        mapa, lista_historico = st.columns([3, 2])
        with mapa:
            st.markdown(f"**Onde avalia** (verde) **e o top {n}** (terracota)")
            avaliados = locais.loc[modelo.treino.loc[modelo.treino["user_id"] == usuario_demo, "gmap_id"], ["latitude", "longitude"]].assign(cor=SALVIA, tamanho=500)
            recomendados = locais.loc[topo["gmap_id"], ["latitude", "longitude"]].assign(cor=TERRACOTA, tamanho=350)
            pontos = pd.concat([avaliados, recomendados]).dropna(subset=["latitude", "longitude"])
            st.map(pontos, latitude="latitude", longitude="longitude", color="cor", size="tamanho", height=300)
        with lista_historico:
            st.markdown("**Locais que avaliou, das maiores notas para as menores**")
            st.dataframe(historico.head(12), hide_index=True, height=300, width="stretch")

        st.html(ESTILO_PRATELEIRA)
        for linha_demo in linhas_demo:
            tabela_demo = linha_demo["tabela"]
            if not len(tabela_demo):
                continue
            previstas = modelo.prever_nota([usuario_demo] * len(tabela_demo), tabela_demo["gmap_id"].tolist())
            cartoes = "".join(
                cartao_html(registro, posicao, rotulo_categorias(locais.at[registro["gmap_id"], "category"], quantidade=2), nota)
                for posicao, (registro, nota) in enumerate(zip(tabela_demo.to_dict("records"), previstas), start=1)
            )
            st.markdown(f"### {linha_demo['titulo']}")
            st.html(f'<div class="prateleira">{cartoes}</div>')
        st.caption(
            "Compatível = pontuação do modelo × 100. ★ = nota prevista (escore do local mais o viés do usuário). "
            "NOVO = local sem avaliações, que entra pela cota ou pela pontuação."
        )

# ---------------------------------------------------------------- Cenário 1
with aba_antigo:
    st.subheader("Recomendação para quem já avaliou locais")
    st.caption(f"Pesos: {pesos_em_texto(configuracao['pesos_cenario1'])}. A lista reserva {configuracao['cota_novos']} posição a um local novo.")

    def sortear():
        frequentes = modelo.avaliacoes_por_usuario.index[modelo.avaliacoes_por_usuario >= 5]
        sorteado = np.random.default_rng().choice(frequentes.to_numpy())
        st.session_state["busca_antigo"] = str(numeracao.numero(sorteado))

    coluna_busca, coluna_botao = st.columns([3, 1], vertical_alignment="bottom")
    texto = coluna_busca.text_input("Número do usuário", key="busca_antigo", placeholder=f"de 1 a {numero_br(len(numeracao))}")
    coluna_botao.button("Sortear", on_click=sortear, help="Sorteia um usuário com 5 ou mais avaliações.", width="stretch")

    usuario = numeracao.buscar(texto)
    if not texto.strip():
        aviso("Digite o número de um usuário ou clique em Sortear.")
    elif usuario is None:
        st.error(f"Usuário não encontrado: os números vão de 1 a {numero_br(len(numeracao))}.")
    else:
        historico = historico_do_usuario(modelo, usuario)
        cidades = cidades_do_usuario(modelo, usuario)
        resumo = resumo_do_perfil(modelo, usuario)
        st.markdown(f"### {numeracao.rotulo(usuario)}")
        colunas = st.columns(3)
        colunas[0].metric("Avaliações", numero_br(len(historico)))
        colunas[1].metric("Nota média", numero_br(historico["Nota"].mean(), 1))
        colunas[2].metric("Cidades", numero_br(len(cidades)))
        linhas = []
        if resumo["gosta"]:
            linhas.append(f"**Gosta mais de:** {', '.join(resumo['gosta'])}.")
        if resumo["evita"]:
            linhas.append(f"**Gosta menos de:** {', '.join(resumo['evita'])}.")
        if not linhas:
            linhas.append("O perfil é neutro: as notas não diferenciam um tipo de local de outro.")
        linhas.append("**Cidades:** " + ", ".join(f"{cidade} ({quantidade})" for cidade, quantidade in cidades.items()) + ".")
        st.markdown("  \n".join(linhas))
        with st.expander(f"Histórico ({numero_br(len(historico))} avaliações)"):
            st.dataframe(historico, hide_index=True, width="stretch")

        st.markdown(f"#### Top {n}")
        lista = modelo.recomendar(usuario, n=n)
        mostrar(tabela_de_locais(lista, locais, modelo, usuario))
        st.caption("A nota prevista é o escore do local mais o viés do usuário, de 1 a 5.")

# ---------------------------------------------------------------- Cenário 2
with aba_novo:
    st.subheader("Recomendação para quem ainda não avaliou nada")
    st.caption(f"Pesos: {pesos_em_texto(configuracao['pesos_cenario2'])}. Todos os campos são opcionais.")
    with st.form("form_novo"):
        coluna_a, coluna_b = st.columns(2)
        cidade = coluna_a.selectbox("Cidade", [NAO_INFORMAR] + recursos["cidades"])
        preco = coluna_b.selectbox("Preço", [NAO_INFORMAR] + list(NIVEIS_DE_PRECO.values()), help="Filtra pelo nível de preço do Google.")
        categorias = st.multiselect("Categorias de que gosta", list(recursos["categorias"]), placeholder="Escolha uma ou mais")
        filtrar = st.checkbox("Usar as categorias como filtro (os locais delas vêm primeiro)")
        atributos = st.multiselect("Atributos desejados", list(recursos["atributos"]), placeholder="Escolha uma ou mais")
        exemplo = st.selectbox("Um local de que gosta", list(recursos["exemplos"]), index=None, placeholder="Escolha ou digite o nome")
        if st.form_submit_button("Recomendar", type="primary"):
            st.session_state["pedido_novo"] = {
                "cidade": None if cidade == NAO_INFORMAR else cidade,
                "preco": None if preco == NAO_INFORMAR else list(NIVEIS_DE_PRECO.values()).index(preco) + 1,
                "categorias": [recursos["categorias"][rotulo] for rotulo in categorias] or None,
                "rotulos_categorias": categorias,
                "filtrar": filtrar,
                "atributos": atributos_declarados([recursos["atributos"][rotulo] for rotulo in atributos]),
                "rotulos_atributos": atributos,
                "exemplo": None if exemplo is None else recursos["exemplos"][exemplo],
                "rotulo_exemplo": exemplo,
            }

    pedido = st.session_state.get("pedido_novo")
    if pedido is not None:
        usado = []
        if pedido["cidade"]:
            usado.append(f"cidade {pedido['cidade']}")
        if pedido["rotulos_categorias"]:
            modo = "como filtro" if pedido["filtrar"] else "como preferência"
            usado.append(f"categorias {', '.join(pedido['rotulos_categorias'])} ({modo})")
        if pedido["rotulos_atributos"]:
            usado.append(f"atributos {', '.join(pedido['rotulos_atributos'])}")
        if pedido["preco"]:
            usado.append(f"preço {NIVEIS_DE_PRECO[pedido['preco']]}")
        if pedido["rotulo_exemplo"]:
            usado.append(f"local de exemplo {pedido['rotulo_exemplo']}")
        if usado:
            st.markdown("**Usado na lista:** " + "; ".join(usado) + ".")
        else:
            aviso("Nada foi informado: a lista segue a qualidade e a popularidade dos locais, sem localização nem gosto.")
        lista = modelo.recomendar_usuario_novo(
            cidade=pedido["cidade"],
            categorias=pedido["categorias"],
            atributos=pedido["atributos"],
            local_exemplo=pedido["exemplo"],
            preco=pedido["preco"],
            n=n,
            filtrar_categorias=pedido["filtrar"],
        )
        for aviso in lista.attrs["avisos"]:
            st.warning(aviso)
        st.markdown(f"#### Top {n}")
        mostrar(tabela_de_locais(lista, locais))

# ---------------------------------------------------------------- Cenário 3
with aba_local:
    st.subheader("Para quem recomendar um local novo")
    st.caption(
        f"Para a lista de usuários, conteúdo {numero_br(configuracao['pesos_cenario3']['alfa'], 1)} e localização "
        f"{numero_br(configuracao['pesos_cenario3']['gama'], 1)}, com o perfil centrado na nota 3. "
        "Para a posição na lista de um usuário, os pesos do cenário 1."
    )
    fonte = st.radio("Local", ["Escolher um local novo da base", "Cadastrar um local"], horizontal=True)
    cadastro = None
    if fonte == "Escolher um local novo da base":
        novos = locais.loc[modelo_c3.locais_novos]
        rotulos = {
            f"{nome} — {cidade if isinstance(cidade, str) else 'sem cidade'} ({'real' if recursos['origem_novos'].get(gmap_id) == 'natural' else 'simulado'})": gmap_id
            for gmap_id, nome, cidade in zip(novos.index, novos["name"], novos["cidade"])
        }
        escolhido = st.selectbox("Local novo", sorted(rotulos), help="Real: local sem avaliações até o corte. Simulado: local antigo com as avaliações escondidas.")
        cadastro = cadastro_do_local(locais.loc[rotulos[escolhido]])
    else:
        with st.form("form_local"):
            nome = st.text_input("Nome do local", placeholder="Ex.: Café da Praça")
            coluna_a, coluna_b = st.columns(2)
            cidade = coluna_a.selectbox("Cidade", [NAO_INFORMAR] + recursos["cidades"])
            outra = coluna_b.text_input("Ou outra cidade", help="Para uma cidade que não está na base.")
            categorias = st.multiselect("Categorias", list(recursos["categorias"]), placeholder="Escolha uma ou mais")
            atributos = st.multiselect("Atributos", list(recursos["atributos"]), placeholder="Escolha uma ou mais")
            coluna_a, coluna_b = st.columns(2)
            latitude = coluna_a.number_input("Latitude (opcional)", value=None, min_value=40.0, max_value=46.0, format="%.5f")
            longitude = coluna_b.number_input("Longitude (opcional)", value=None, min_value=-112.0, max_value=-103.0, format="%.5f")
            if st.form_submit_button("Cadastrar", type="primary"):
                st.session_state["cadastro_local"] = {
                    "name": nome.strip() or "Local cadastrado",
                    "category": [recursos["categorias"][rotulo] for rotulo in categorias],
                    "MISC": atributos_declarados([recursos["atributos"][rotulo] for rotulo in atributos]) or {},
                    "cidade": outra.strip() or (None if cidade == NAO_INFORMAR else cidade),
                    "latitude": latitude,
                    "longitude": longitude,
                }
        cadastro = st.session_state.get("cadastro_local")
        if cadastro is None:
            aviso("Preencha o cadastro e clique em Cadastrar.")

    if cadastro is not None:
        tem_coordenada = cadastro["latitude"] is not None and cadastro["longitude"] is not None and np.isfinite(cadastro["latitude"]) and np.isfinite(cadastro["longitude"])
        cidade_conhecida = isinstance(cadastro["cidade"], str) and (locais["cidade"] == cadastro["cidade"]).any()
        atributos_do_local = [valor for valores in (cadastro["MISC"] or {}).values() if valores is not None for valor in valores]
        descricao = [f"**{cadastro['name']}**", cadastro["cidade"] or "sem cidade", rotulo_categorias(cadastro["category"], quantidade=5) or "sem categorias"]
        st.markdown(" · ".join(descricao))
        sem_conteudo = not cadastro["category"] and not atributos_do_local
        if sem_conteudo and not tem_coordenada and not cidade_conhecida:
            st.warning("Cadastro vazio: sem categorias, atributos, cidade conhecida nem coordenada, todos os usuários empatam. Informe ao menos a cidade ou uma categoria.")
        elif not tem_coordenada and not cidade_conhecida:
            if isinstance(cadastro["cidade"], str):
                st.warning(f"{cadastro['cidade']} não tem locais na base e não há coordenada: o componente de local fica zero e a lista segue só o conteúdo.")
            else:
                st.warning("Sem cidade nem coordenada: o componente de local fica zero e a lista segue só o conteúdo.")
        elif sem_conteudo:
            st.warning("Sem categorias nem atributos: o conteúdo fica neutro para todos e a lista segue só a localização.")

        st.markdown(f"#### (A) Os {n} usuários mais indicados")
        indicados = modelo_c3.usuarios_para_local_novo(cadastro, n=n)
        vetor = modelo_c3.vetorizador.transform([cadastro])
        tabela = pd.DataFrame(
            {
                "Posição": np.arange(1, len(indicados) + 1),
                "Usuário": [numeracao.rotulo(usuario) for usuario in indicados["user_id"]],
                "Pontuação": [numero_br(100 * valor, 1) for valor in indicados["pontuacao"]],
                "Conteúdo": (100 * indicados["conteudo"]).round().to_numpy(),
                "Localização": (100 * indicados["local"]).round().to_numpy(),
                "Por quê": [motivo_para_local_novo(modelo_c3, usuario, vetor, cadastro["cidade"]) for usuario in indicados["user_id"]],
            }
        )
        mostrar(tabela)

        st.markdown("#### (B) Entra na lista de um usuário?")
        rotulo_para_id = {numeracao.rotulo(usuario): usuario for usuario in indicados["user_id"]}
        coluna_a, coluna_b = st.columns(2)
        da_lista = coluna_a.selectbox("Um dos usuários acima", list(rotulo_para_id))
        outro = coluna_b.text_input("Ou o número de outro usuário", key="busca_local")
        usuario = rotulo_para_id[da_lista]
        if outro.strip():
            usuario = numeracao.buscar(outro)
            if usuario is None or usuario not in modelo_c3._linha_perfil.index:
                st.error(f"Usuário não encontrado: os números vão de 1 a {numero_br(len(numeracao))}.")
                usuario = None
        if usuario is not None:
            decisao = modelo_c3.posicao_local_novo(usuario, cadastro, n=n)
            texto = (
                f"Na lista do **{numeracao.rotulo(usuario)}**, o local ficaria em **{numero_br(decisao['posicao'])}º** "
                f"de {numero_br(decisao['total'])} candidatos, com pontuação {numero_br(100 * decisao['pontuacao'], 1)}."
            )
            if decisao["recomendar"]:
                aviso(texto + f" **Recomendar:** entra no top {n} por mérito.")
            else:
                aviso(texto + f" **Não recomendar por mérito:** fica fora do top {n}. A cota de 1 local novo ainda pode levá-lo à lista, se ele for o local novo mais bem pontuado para essa pessoa.")
