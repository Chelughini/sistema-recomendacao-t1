"""Constrói os gráficos da apresentação em `apresentacao/graficos/`, no tema dos slides.

Material da apresentação (todos em `scripts/`):

- `graficos_apresentacao.py` (este): os gráficos, a partir dos dados e dos modelos congelados;
- `capturar_telas.py`: as telas da interface (`figuras/50_` a `53_`);
- `gerar_ppt.py`: os slides, que usam os dois acima.

O tema (cores, fonte e fundo branco) está em `src/tema_apresentacao.py`, o mesmo do gerador dos slides.
Os gráficos do relatório (`figuras/10_` a `43_`) continuam saindo dos notebooks 01 a 04.

Os gráficos de estimação (validação) e de performance (teste) refazem as contas dos notebooks 03 e 04,
com as mesmas funções, modelos congelados e sementes; cada parte confere que os números batem. Nada é
escolhido aqui: o teste só é recalculado para desenhar.

Rodar a partir da raiz do projeto, depois dos notebooks 01 a 03:

    python scripts/graficos_apresentacao.py                 # todos (alguns minutos, por causa do teste)
    python scripts/graficos_apresentacao.py base teoria     # só algumas partes
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.avaliacao import cenario1, cenario2, cenario3, pares_roc_consumo, pares_roc_gosto  # noqa: E402
from src.dados import indice_gini  # noqa: E402
from src.features import VetorizadorConteudo  # noqa: E402
from src.graficos import eixo_br, numero_br  # noqa: E402
from src.interface import NumeracaoUsuarios, pesos_do_perfil, rotulo_categoria  # noqa: E402
from src.metricas import avaliar, curva_roc_media, intervalo, montar_protocolo  # noqa: E402
from src.recomendador import calcular_componentes, modelo_ponderado  # noqa: E402
from src.tema_apresentacao import CORES, ESCALA, MOSTARDA, SALVIA, TERRACOTA, aplicar_tema, salvar  # noqa: E402

PASTA_PROCESSADOS = RAIZ / "data" / "processed"
PASTA_CONJUNTOS = PASTA_PROCESSADOS / "conjuntos"
PASTA_MODELOS = RAIZ / "modelos"
NOMES_PESOS = ["alfa", "beta", "gama", "delta"]
PESOS_METODO3 = (0.0, 0.3, 0.0, 0.7)  # escore + popularidade, escolhidos na validação (03_modelo, cenário 2)
USUARIO_EXEMPLO = "12369"  # o mesmo da aba Demonstração e dos slides
PARTES = ["base", "teoria", "divisao", "estimacao", "performance"]


def inteiro(valor):
    return f"{valor:,}".replace(",", ".")


def percentual(valor, casas=1):
    return f"{100 * valor:.{casas}f}%".replace(".", ",")


def confere(obtido, esperado, nome):
    """Trava: o número recalculado tem de ser o do relatório."""
    if abs(obtido - esperado) > 5e-5:
        raise AssertionError(f"{nome}: {obtido:.4f}, esperado {esperado:.4f}")


def gravar(figura, nome):
    caminho = salvar(figura, nome)
    plt.close(figura)
    print(f"  {caminho.relative_to(RAIZ)}")


class Dados:
    """Carrega cada arquivo uma vez, só quando alguma parte precisa dele."""

    def __init__(self):
        self._cache = {}

    def _ler(self, chave, funcao):
        if chave not in self._cache:
            self._cache[chave] = funcao()
        return self._cache[chave]

    @property
    def avaliacoes(self):
        return self._ler("avaliacoes", lambda: pd.read_parquet(PASTA_PROCESSADOS / "avaliacoes.parquet"))

    @property
    def locais(self):
        return self._ler("locais", lambda: pd.read_parquet(PASTA_PROCESSADOS / "locais.parquet"))

    def conjunto(self, nome):
        return self._ler(nome, lambda: pd.read_parquet(PASTA_CONJUNTOS / f"{nome}.parquet"))

    @property
    def divisao(self):
        return self._ler("divisao", lambda: json.loads((PASTA_CONJUNTOS / "divisao.json").read_text(encoding="utf-8")))

    @property
    def cenario1_json(self):
        return self._ler("cenario1_json", lambda: json.loads((PASTA_MODELOS / "cenario1.json").read_text(encoding="utf-8")))

    @property
    def modelo(self):
        return self._ler("modelo", lambda: joblib.load(PASTA_MODELOS / "recomendador.joblib"))

    @property
    def modelo_c3(self):
        return self._ler("modelo_c3", lambda: joblib.load(PASTA_MODELOS / "recomendador_c3.joblib"))

    @property
    def abertos(self):
        return ~(self.locais["fechado_perm"] | self.locais["fechado_temp"]).to_numpy()


def barras_verticais(eixo, rotulos, valores, cores, etiquetas, tamanho_etiqueta=14):
    barras = eixo.bar(rotulos, valores, color=cores, width=0.62)
    eixo.bar_label(barras, labels=etiquetas, padding=4, fontsize=tamanho_etiqueta, color=CORES["texto"])
    eixo.set_ylim(0, max(valores) * 1.15)
    eixo.grid(axis="x", visible=False)
    eixo_br(eixo.yaxis)


def grafico_intervalos(resultados, metricas, nome_arquivo, destaque, altura_por_linha=0.5):
    """Média e IC de 95% de cada método, lado a lado por métrica; o destaque em terracota."""
    nomes = list(resultados)[::-1]
    figura, eixos = plt.subplots(1, len(metricas), figsize=(12, altura_por_linha * len(nomes) + 1.4), sharey=True)
    eixos = np.atleast_1d(eixos)
    for eixo, (metrica, titulo) in zip(eixos, metricas):
        medias, inferiores, superiores = (np.array(v) for v in zip(*(intervalo(resultados[nome], metrica) for nome in nomes)))
        cores = [TERRACOTA if nome == destaque else SALVIA for nome in nomes]
        eixo.errorbar(medias, range(len(nomes)), xerr=[medias - inferiores, superiores - medias], fmt="none", ecolor=cores, elinewidth=2.5)
        eixo.scatter(medias, range(len(nomes)), color=cores, s=[140 if nome == destaque else 60 for nome in nomes], zorder=3)
        eixo.axvline(medias[nomes.index(destaque)], color=CORES["eixo"], linewidth=1.5)
        eixo.set_title(titulo)
        eixo.grid(axis="y", visible=False)
        eixo_br(eixo.xaxis, 2)
    eixos[0].set_yticks(range(len(nomes)), nomes)
    for rotulo in eixos[0].get_yticklabels():
        if rotulo.get_text() == destaque:
            rotulo.set_color(TERRACOTA)
            rotulo.set_fontweight("bold")
    figura.tight_layout()
    gravar(figura, nome_arquivo)


# ---------------------------------------------------------------- 1. Base de dados
def base(d):
    avaliacoes, locais = d.avaliacoes, d.locais

    notas = avaliacoes["rating"].value_counts().sort_index()
    figura, eixo = plt.subplots(figsize=(8, 4.2))
    barras_verticais(eixo, notas.index, notas.values, [SALVIA] * 3 + [TERRACOTA] * 2, [percentual(v / len(avaliacoes)) for v in notas.values])
    eixo.set_xlabel("nota")
    eixo.set_ylabel("avaliações")
    gravar(figura, "base_notas")

    por_usuario = avaliacoes.groupby("user_id").size()
    limiares = [1, 2, 3, 5, 10, 20, 50]
    usuarios = [int((por_usuario >= k).sum()) for k in limiares]
    figura, eixo = plt.subplots(figsize=(8, 4.2))
    barras_verticais(eixo, [f"≥ {k}" for k in limiares], usuarios, [TERRACOTA] + [SALVIA] * 6, [inteiro(v) for v in usuarios], 13)
    eixo.set_xlabel("usuários com ao menos k avaliações")
    gravar(figura, "base_atividade")

    por_local = avaliacoes.groupby("gmap_id").size().sort_values(ascending=False)
    acumulado = por_local.cumsum().to_numpy() / por_local.sum()
    fracao = np.arange(1, len(por_local) + 1) / len(por_local)
    vinte = acumulado[int(np.ceil(0.2 * len(por_local))) - 1]
    figura, eixo = plt.subplots(figsize=(8, 4.2))
    eixo.plot(100 * fracao, 100 * acumulado, color=TERRACOTA)
    eixo.plot([20, 20, 0], [0, 100 * vinte, 100 * vinte], color=SALVIA, linewidth=1.5, linestyle="--")
    eixo.scatter([20], [100 * vinte], color=TERRACOTA, s=80, zorder=3)
    eixo.annotate(f"20% dos locais: {percentual(vinte, 0)} das avaliações", (20, 100 * vinte), xytext=(14, -26), textcoords="offset points", fontsize=14)
    eixo.set_xlabel("% dos locais, do mais avaliado ao menos")
    eixo.set_ylabel("% acumulada das avaliações")
    eixo.set_xlim(0, 100)
    eixo.set_ylim(0, 102)
    gravar(figura, "base_concentracao")
    print(f"  Gini {numero_br(indice_gini(por_local), 3)}; 20% dos locais com {percentual(vinte)} das avaliações")

    juntas = avaliacoes.merge(locais[["gmap_id", "categoria_principal"]], on="gmap_id")
    categorias = (
        juntas.groupby("categoria_principal").agg(avaliacoes=("rating", "size"), nota=("rating", "mean"))
        .sort_values("avaliacoes", ascending=False).head(12)
    )
    figura, eixo = plt.subplots(figsize=(9, 5.4))
    ordem = categorias.index[::-1]
    barras = eixo.barh([rotulo_categoria(n) for n in ordem], categorias["avaliacoes"].to_numpy()[::-1],
                       color=[TERRACOTA if n == "Fast food restaurant" else SALVIA for n in ordem], height=0.62)
    eixo.bar_label(barras, labels=[f"nota {numero_br(n, 2)}" for n in categorias["nota"].to_numpy()[::-1]], padding=6, fontsize=12)
    eixo.set_xlabel("avaliações")
    eixo.set_xlim(0, categorias["avaliacoes"].max() * 1.22)
    eixo.grid(axis="y", visible=False)
    eixo_br(eixo.xaxis)
    gravar(figura, "base_categorias")

    resumo = (
        avaliacoes.groupby("gmap_id").agg(avaliacoes=("rating", "size"), nota=("rating", "mean"))
        .join(locais.set_index("gmap_id")[["latitude", "longitude"]]).sort_values("avaliacoes", ascending=False)
    )
    figura, eixo = plt.subplots(figsize=(9, 6))
    pontos = eixo.scatter(resumo["longitude"], resumo["latitude"], s=10 + resumo["avaliacoes"] / 10, c=resumo["nota"].clip(3, 5),
                          cmap=ESCALA, vmin=3, vmax=5, linewidths=0.4, edgecolors="white")
    eixo.set_aspect(1 / np.cos(np.radians(43)))
    eixo.set_xlabel("longitude")
    eixo.set_ylabel("latitude")
    eixo.set_xticks(range(-111, -103))
    eixo.set_yticks(range(41, 46))
    barra = figura.colorbar(pontos, ax=eixo, shrink=0.6, label="nota média (tamanho = avaliações)")
    barra.outline.set_visible(False)
    eixo_br(barra.ax.yaxis, 1)
    gravar(figura, "base_mapa")

    por_ano = avaliacoes.groupby(avaliacoes["data"].dt.year).size()
    figura, eixo = plt.subplots(figsize=(9, 4.2))
    eixo.bar(por_ano.index, por_ano.values, color=[TERRACOTA if ano >= 2020 else SALVIA for ano in por_ano.index], width=0.65)
    eixo.set_xticks(por_ano.index, [str(a) for a in por_ano.index], fontsize=11)
    eixo.set_ylabel("avaliações")
    eixo.grid(axis="x", visible=False)
    eixo_br(eixo.yaxis)
    gravar(figura, "base_por_ano")

    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    completos = avaliacoes[avaliacoes["data"].dt.year.between(2017, 2019)]
    por_mes = completos.groupby(completos["data"].dt.month).size().reindex(range(1, 13), fill_value=0)
    figura, eixo = plt.subplots(figsize=(9, 4.2))
    eixo.bar(meses, por_mes.values, color=[TERRACOTA if mes in (6, 7, 8) else SALVIA for mes in por_mes.index], width=0.65)
    eixo.set_ylabel("avaliações, 2017 a 2019")
    eixo.grid(axis="x", visible=False)
    eixo_br(eixo.yaxis)
    gravar(figura, "base_por_mes")
    print(f"  julho / fevereiro = {numero_br(por_mes[7] / por_mes[2], 2)}")


# ---------------------------------------------------------------- 2. Conceitos teóricos
def teoria(d):
    modelo, locais = d.modelo, d.locais

    escores = modelo.escores[modelo.escores["avaliacoes"] > 0].sort_values("avaliacoes")
    media_geral = modelo.parametros["C"]
    figura, eixo = plt.subplots(figsize=(8.5, 5.4))
    pontos = eixo.scatter(escores["media"], escores["escore"], c=escores["avaliacoes"], cmap=ESCALA,
                          norm=LogNorm(vmin=1, vmax=escores["avaliacoes"].max()), s=22, linewidths=0.3, edgecolors="white")
    eixo.plot([1, 5], [1, 5], color=CORES["eixo"], linewidth=1.5)
    eixo.axhline(media_geral, color=SALVIA, linewidth=1.5, linestyle="--")
    eixo.annotate(f"média geral: {numero_br(media_geral, 2)}", (1.05, media_geral + 0.07), color=SALVIA, fontsize=13)
    eixo.annotate("se fosse a média simples", (3.15, 2.75), color=CORES["suave"], fontsize=12, rotation=33)
    barra = figura.colorbar(pontos, ax=eixo, pad=0.02)
    barra.set_label("avaliações do local")
    barra.outline.set_visible(False)
    barra.set_ticks([1, 10, 100, 1000], labels=["1", "10", "100", "1.000"])
    barra.minorticks_off()
    eixo.set_xlabel("média simples das notas")
    eixo.set_ylabel("escore (média bayesiana)")
    eixo_br(eixo.xaxis, 1)
    eixo_br(eixo.yaxis, 1)
    gravar(figura, "teoria_escore")

    # Perfil do usuário de exemplo: o mesmo cálculo da aba Demonstração (src.interface.pesos_do_perfil).
    usuario = NumeracaoUsuarios(modelo._linha_perfil.index).buscar(USUARIO_EXEMPLO)
    pesos = pesos_do_perfil(modelo, usuario).sort_values("peso")
    figura, eixo = plt.subplots(figsize=(9, 5))
    eixo.barh(pesos["caracteristica"], pesos["peso"], color=[TERRACOTA if v > 0 else SALVIA for v in pesos["peso"]], height=0.62)
    eixo.axvline(0, color=CORES["suave"], linewidth=1.2)
    eixo.xaxis.set_major_formatter(plt.NullFormatter())
    eixo.grid(axis="both", visible=False)
    eixo.legend(handles=[Patch(color=TERRACOTA, label="gosta mais que a própria média"), Patch(color=SALVIA, label="gosta menos")],
                loc="upper center", bbox_to_anchor=(0.5, -0.04), ncols=2)
    gravar(figura, "teoria_perfil_usuario")

    vetorizador = VetorizadorConteudo().fit(locais[locais["gmap_id"].isin(d.conjunto("treino")["gmap_id"])])
    matriz = vetorizador.transform(locais)
    similaridades = (matriz @ matriz.T).toarray()
    abertos = d.abertos
    contagem_treino = d.conjunto("treino").groupby("gmap_id").size()

    def exemplo(categoria):
        candidatos = locais[(locais["categoria_principal"] == categoria) & abertos]
        return candidatos.assign(n=candidatos["gmap_id"].map(contagem_treino)).sort_values("n", ascending=False).index[0]

    figura, eixos = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True)
    for eixo, (tipo, categoria) in zip(eixos, [("Pizzaria", "Pizza restaurant"), ("Café", "Coffee shop"), ("Bar", "Bar")]):
        linha_exemplo = exemplo(categoria)
        linha = similaridades[linha_exemplo].copy()
        linha[linha_exemplo] = -1
        linha[~abertos] = -1
        ordem = np.argsort(-linha, kind="stable")[:5]
        cidades = [locais.at[i, "cidade"] if isinstance(locais.at[i, "cidade"], str) else "sem cidade" for i in ordem]
        rotulos = [f"{locais.at[i, 'name'][:26].strip()}, {cidade}".replace("$", r"\$") for i, cidade in zip(ordem, cidades)]
        posicoes = np.arange(5)[::-1]
        eixo.barh(posicoes, linha[ordem], color=SALVIA, height=0.6)
        eixo.set_yticks(posicoes, rotulos, fontsize=11)
        eixo.set_title(f"{tipo}: {locais.at[linha_exemplo, 'name']}".replace("$", r"\$"), fontsize=14)
        eixo.set_xlim(0, 1)
        eixo.grid(axis="y", visible=False)
        eixo_br(eixo.xaxis, 1)
    eixos[-1].set_xlabel("similaridade de conteúdo (cosseno)")
    figura.tight_layout()
    gravar(figura, "teoria_vizinhos")


# ---------------------------------------------------------------- 3. Treino e teste
def divisao(d):
    avaliacoes = d.avaliacoes
    corte_validacao = pd.Timestamp(d.divisao["corte_validacao"]).to_period("M").to_timestamp()
    corte_teste = pd.Timestamp(d.divisao["corte_teste"]).to_period("M").to_timestamp()
    mensal = avaliacoes.groupby(avaliacoes["data"].dt.to_period("M")).size()
    mensal = mensal[mensal.index >= pd.Period("2015-01")]
    meses = mensal.index.to_timestamp()
    cores = np.where(meses >= corte_teste, TERRACOTA, np.where(meses >= corte_validacao, MOSTARDA, SALVIA))
    figura, eixo = plt.subplots(figsize=(11, 4.4))
    eixo.bar(meses, mensal.values, width=26, color=cores)
    eixo.legend(handles=[Patch(color=SALVIA, label="treino"), Patch(color=MOSTARDA, label="validação"), Patch(color=TERRACOTA, label="teste")],
                loc="upper left", ncols=3, fontsize=13)
    eixo.set_ylabel("avaliações por mês")
    eixo.set_ylim(0, mensal.max() * 1.18)
    eixo.grid(axis="x", visible=False)
    eixo_br(eixo.yaxis)
    gravar(figura, "divisao_tempo")


# ---------------------------------------------------------------- 4. Estimação (validação)
def estimacao(d):
    grade = pd.read_csv(sorted((PASTA_MODELOS / "grades").glob("etapa2_pesos_final_*.csv"))[0])
    grade = grade[grade["alfa"] >= 0.1 - 1e-9]
    pesos_finais = tuple(d.cenario1_json["pesos"][nome] for nome in NOMES_PESOS)
    escolhida = grade[grade[NOMES_PESOS].sub(list(pesos_finais)).abs().sum(axis=1) < 1e-9].iloc[0]
    confere(escolhida["conversao"], 0.0739, "conversão da combinação escolhida")
    confere(escolhida["auc_gosto"], 0.5850, "AUC de gosto da combinação escolhida")
    limite = 0.95 * grade["conversao"].max()
    aptas = grade["conversao"] >= limite
    figura, eixo = plt.subplots(figsize=(9, 5.4))
    eixo.scatter(grade.loc[~aptas, "conversao"], grade.loc[~aptas, "auc_gosto"], color=CORES["eixo"], s=26, label="abaixo de 95% da melhor conversão")
    eixo.scatter(grade.loc[aptas, "conversao"], grade.loc[aptas, "auc_gosto"], color=SALVIA, s=40, label="aptas")
    eixo.scatter([escolhida["conversao"]], [escolhida["auc_gosto"]], color=TERRACOTA, s=180, zorder=3, label="escolhida")
    eixo.axvline(limite, color=SALVIA, linewidth=1.5, linestyle="--")
    eixo.set_xlabel("taxa de conversão@10")
    eixo.set_ylabel("AUC de gosto")
    eixo.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncols=3)
    eixo_br(eixo.xaxis, 2)
    eixo_br(eixo.yaxis, 2)
    gravar(figura, "estimacao_pesos")

    treino, locais = d.conjunto("treino"), d.locais
    protocolo = montar_protocolo(treino, d.conjunto("validacao"), locais, ["antigo"])
    componentes = calcular_componentes(treino, locais, protocolo.usuarios, protocolo.candidatos, **d.cenario1_json["configuracao"])

    def sem(indice):
        restantes = [0.0 if i == indice else peso for i, peso in enumerate(pesos_finais)]
        return tuple(peso / sum(restantes) for peso in restantes)

    nomes = ["conteúdo", "escore", "localização", "popularidade"]
    casos = {"modelo escolhido": pesos_finais}
    casos |= {f"só {nome}": tuple(1.0 if j == i else 0.0 for j in range(4)) for i, nome in enumerate(nomes)}
    casos |= {f"sem {nome}": sem(i) for i, nome in enumerate(nomes)}
    ablacao = {nome: avaliar(protocolo, modelo_ponderado(componentes, pesos)) for nome, pesos in casos.items()}
    confere(ablacao["modelo escolhido"].resumo()["conversao"], 0.0739, "conversão do modelo na ablação")
    grafico_intervalos(ablacao, [("conversao", "Taxa de conversão@10"), ("auc_gosto", "AUC de gosto")], "estimacao_ablacao", "modelo escolhido")


# ---------------------------------------------------------------- 5. Performance (teste)
def performance(d):
    modelo, modelo_c3, locais = d.modelo, d.modelo_c3, d.locais
    treino_total, teste = d.conjunto("treino_total"), d.conjunto("teste")
    metricas = [("conversao", "Taxa de conversão@10"), ("auc_gosto", "AUC de gosto")]

    protocolo_c1, modelos_c1, resultados_c1 = cenario1(modelo, treino_total, teste, locais)
    confere(resultados_c1["modelo"].resumo()["conversao"], 0.0520, "conversão do cenário 1")
    confere(resultados_c1["modelo"].resumo()["auc_gosto"], 0.5542, "AUC de gosto do cenário 1")
    grafico_intervalos(resultados_c1, metricas, "performance_usuario_antigo", "modelo")

    _, _, resultados_c2 = cenario2(modelo, treino_total, teste, locais, PESOS_METODO3)
    base_c2 = "5. modelo: + categorias com peso"
    confere(resultados_c2[base_c2].resumo()["conversao"], 0.0452, "conversão do cenário 2")
    grafico_intervalos(resultados_c2, metricas, "performance_usuario_novo", base_c2)

    abertos = set(locais.loc[d.abertos, "gmap_id"])
    novos = d.conjunto("locais_novos")
    no_teste = novos["conjunto"] == "teste"
    novos_teste = {origem: [g for g in novos.loc[no_teste & (novos["origem"] == origem), "gmap_id"] if g in abertos] for origem in ["natural", "simulado"]}
    resultados_c3 = cenario3(modelo_c3, d.conjunto("treino_total_c3"), teste, locais, novos_teste)
    confere(resultados_c3["natural"]["ordenar"]["modelo"].resumo()["auc_consumo"], 0.9209, "AUC de consumo do cenário 3")

    figura, eixos = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
    for eixo, origem, titulo in zip(eixos, ["natural", "simulado"], ["AUC de consumo, locais reais", "AUC de consumo, locais simulados"]):
        ordenar = resultados_c3[origem]["ordenar"]
        nomes = list(ordenar)[::-1]
        medias, inferiores, superiores = (np.array(v) for v in zip(*(intervalo(ordenar[nome], "auc_consumo") for nome in nomes)))
        cores = [TERRACOTA if nome == "modelo" else SALVIA for nome in nomes]
        eixo.errorbar(medias, range(len(nomes)), xerr=[medias - inferiores, superiores - medias], fmt="none", ecolor=cores, elinewidth=2.5)
        eixo.scatter(medias, range(len(nomes)), color=cores, s=[140 if nome == "modelo" else 60 for nome in nomes], zorder=3)
        eixo.set_title(titulo)
        eixo.grid(axis="y", visible=False)
        eixo_br(eixo.xaxis, 2)
    eixos[0].set_yticks(range(len(nomes)), nomes)
    figura.tight_layout()
    gravar(figura, "performance_local_novo")

    def curva(protocolo, funcao, tipo):
        pontuacoes = funcao(protocolo.usuarios, protocolo.candidatos)
        pares = pares_roc_gosto(protocolo, pontuacoes) if tipo == "gosto" else pares_roc_consumo(protocolo, pontuacoes)
        return curva_roc_media(pares)

    figura, (eixo_gosto, eixo_consumo) = plt.subplots(1, 2, figsize=(12, 5))
    for nome, cor in [("modelo", TERRACOTA), ("vizinhos por item, combinado", SALVIA), ("popularidade + local", MOSTARDA)]:
        x, y = curva(protocolo_c1, modelos_c1[nome], "gosto")
        eixo_gosto.plot(x, y, color=cor, label=f"{nome} ({numero_br(resultados_c1[nome].resumo()['auc_gosto'], 3)})")
    naturais = resultados_c3["natural"]
    for nome, cor in [("modelo", TERRACOTA), ("só local", SALVIA), ("só conteúdo", MOSTARDA)]:
        x, y = curva(naturais["protocolo"], naturais["ordenar_modelos"][nome], "consumo")
        eixo_consumo.plot(x, y, color=cor, label=f"{nome} ({numero_br(naturais['ordenar'][nome].resumo()['auc_consumo'], 3)})")
    for eixo, titulo in [(eixo_gosto, "Gosto, usuário antigo"), (eixo_consumo, "Consumo, locais novos reais")]:
        eixo.plot([0, 1], [0, 1], color=CORES["eixo"], linewidth=1.5, linestyle="--")
        eixo.set_title(titulo)
        eixo.set_xlabel("taxa de falsos positivos")
        eixo.set_ylabel("taxa de verdadeiros positivos")
        eixo.legend(loc="lower right")
        eixo_br(eixo.xaxis, 1)
        eixo_br(eixo.yaxis, 1)
    figura.tight_layout()
    gravar(figura, "performance_roc")


def main():
    parser = argparse.ArgumentParser(description="Gráficos da apresentação, no tema dos slides.")
    parser.add_argument("partes", nargs="*", choices=PARTES, help=f"partes a gerar (padrão: todas): {', '.join(PARTES)}")
    partes = parser.parse_args().partes or PARTES
    sys.stdout.reconfigure(encoding="utf-8")
    aplicar_tema()
    dados = Dados()
    for parte in partes:
        print(f"{parte}:")
        globals()[parte](dados)


if __name__ == "__main__":
    main()
