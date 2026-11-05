"""Componentes do modelo: escores de produto, perfil do usuário, local e previsão de nota."""

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import normalize

from src.analises import matriz_distancias_km
from src.divisao import MINIMO_USUARIO_ANTIGO, eh_relevante
from src.features import VetorizadorConteudo
from src.metricas import aplicar_cota_de_novos
from src.traducoes import traduzir_token

CENTRO_PADRAO = 3
PERCENTIL_PADRAO = 50
REGULARIZACAO_VIES = 10
PESOS_CONGELADOS = (0.1, 0.2, 0.5, 0.2)
# Cenário 2: os pesos do método 4 (0 / 0,2 / 0,5 / 0,3) com o conteúdo declarado a 0,05 e o resto × 0,95.
PESOS_USUARIO_NOVO = (0.05, 0.19, 0.475, 0.285)


def _media_bayesiana(avaliacoes, medias, m, prior):
    return (avaliacoes * medias + m * prior) / (avaliacoes + m)


def escores_de_produto(treino, locais, percentil=PERCENTIL_PADRAO):
    """Calcula, para cada local, os escores de qualidade e a popularidade, olhando só o treino.

    `escore` é a média bayesiana com prior na média do treino. `escore_cidade` usa como prior a média
    da cidade, ela própria suavizada, para que uma cidade pequena não vire um prior extremo.
    Devolve a tabela, indexada por `gmap_id`, e os parâmetros `C` e `m`.
    """
    agrupado = treino.groupby("gmap_id")["rating"].agg(["size", "mean"])
    tabela = pd.DataFrame(
        {
            "cidade": locais["cidade"].to_numpy(),
            "aberto": ~(locais["fechado_perm"] | locais["fechado_temp"]).to_numpy(),
        },
        index=pd.Index(locais["gmap_id"].to_numpy(), name="gmap_id"),
    )
    tabela["avaliacoes"] = agrupado["size"].reindex(tabela.index, fill_value=0).astype(int)
    tabela["media"] = agrupado["mean"].reindex(tabela.index).fillna(0.0)

    avaliados = tabela["avaliacoes"] > 0
    media_global = treino["rating"].mean()
    m = float(np.percentile(tabela.loc[avaliados, "avaliacoes"], percentil))

    tabela["escore"] = _media_bayesiana(tabela["avaliacoes"], tabela["media"], m, media_global)
    tabela["escore_normalizado"] = (tabela["escore"] - 1) / 4

    soma_cidade = (tabela["avaliacoes"] * tabela["media"]).groupby(tabela["cidade"]).sum()
    total_cidade = tabela["avaliacoes"].groupby(tabela["cidade"]).sum()
    media_cidade = (soma_cidade / total_cidade.where(total_cidade > 0)).fillna(0.0)
    prior_cidade = _media_bayesiana(total_cidade, media_cidade, m, media_global)
    tabela["prior_cidade"] = tabela["cidade"].map(prior_cidade).fillna(media_global)
    tabela["escore_cidade"] = _media_bayesiana(tabela["avaliacoes"], tabela["media"], m, tabela["prior_cidade"])

    abertos_com_cidade = tabela[tabela["aberto"] & tabela["cidade"].notna()]
    tabela["posicao_na_cidade"] = abertos_com_cidade.groupby("cidade")["escore_cidade"].rank(method="min", ascending=False)

    tabela["popularidade"] = _popularidade(tabela)
    return tabela, {"C": float(media_global), "m": m}


def _popularidade(tabela):
    """`log(1 + v) / log(1 + máx v)`; local novo recebe a mediana da cidade, ou do catálogo."""
    avaliacoes = tabela["avaliacoes"]
    valores = np.log1p(avaliacoes) / np.log1p(avaliacoes.max())
    avaliados = avaliacoes > 0
    mediana_cidade = valores[avaliados].groupby(tabela.loc[avaliados, "cidade"]).median()
    substitutos = tabela["cidade"].map(mediana_cidade).fillna(valores[avaliados].median())
    return valores.where(avaliados, substitutos)


def perfis_de_usuarios(treino, vetores, posicao_do_local, centro="fixo"):
    """Monta `p_u = Σ w_ui · x_i`, normalizado em L2, com `w_ui = nota − centro`.

    Com `centro="usuario"`, o centro é a média do usuário; quem não varia as notas usa 3, pois o
    perfil dessas pessoas seria apagado. Quem só deu notas neutras fica com a média simples dos
    vetores. Pesos que se cancelam geram vetor nulo, que resulta em similaridade neutra.
    """
    codigos, usuarios = pd.factorize(treino["user_id"].to_numpy())
    notas = treino["rating"].to_numpy(dtype=float)
    centros = np.full(len(notas), float(CENTRO_PADRAO))
    if centro == "usuario":
        agrupadas = treino.groupby("user_id")["rating"]
        medias = agrupadas.transform("mean").to_numpy()
        variam = (agrupadas.transform("nunique") > 1).to_numpy()
        centros = np.where(variam, medias, CENTRO_PADRAO)
    elif centro != "fixo":
        raise ValueError(f"Centro desconhecido: {centro}")

    pesos = notas - centros
    tem_peso = np.bincount(codigos, np.abs(pesos) > 0, minlength=len(usuarios)) > 0
    pesos = np.where(tem_peso[codigos], pesos, 1.0)
    colunas = treino["gmap_id"].map(posicao_do_local).to_numpy()
    matriz_pesos = sparse.csr_matrix((pesos, (codigos, colunas)), shape=(len(usuarios), vetores.shape[0]))
    perfis = normalize(matriz_pesos @ vetores, norm="l2")
    perfis.eliminate_zeros()
    return perfis, np.asarray(usuarios).astype(str)


def similaridade_conteudo(perfis, vetores):
    """`(cos + 1) / 2` entre perfis e locais; perfil ou vetor vazio dá 0,5, o valor neutro."""
    return (np.asarray((perfis @ vetores.T).todense()) + 1) / 2


def afinidade_cidade(treino, locais, usuarios, candidatos):
    """Fração das avaliações de cada usuário na cidade de cada candidato."""
    cidades = locais.set_index("gmap_id")["cidade"]
    usuarios = np.asarray(usuarios).astype(str)
    posicao_usuario = pd.Series(np.arange(len(usuarios)), index=usuarios)
    do_treino = treino[treino["user_id"].isin(usuarios)]
    totais = do_treino.groupby("user_id").size().reindex(usuarios, fill_value=0).to_numpy(dtype=float)

    com_cidade = do_treino.assign(cidade=do_treino["gmap_id"].map(cidades)).dropna(subset=["cidade"])
    cidades_candidatos = cidades.reindex(candidatos).to_numpy()
    resultado = np.zeros((len(usuarios), len(candidatos)))
    colunas_por_cidade = pd.Series(np.arange(len(candidatos))).groupby(cidades_candidatos).apply(list).to_dict()
    contagens = com_cidade.groupby(["cidade", "user_id"]).size().reset_index(name="n")
    for cidade, grupo in contagens.groupby("cidade"):
        colunas = colunas_por_cidade.get(cidade)
        if colunas is not None:
            linhas = grupo["user_id"].map(posicao_usuario).to_numpy()
            resultado[linhas[:, None], colunas] = grupo["n"].to_numpy(dtype=float)[:, None]
    return np.divide(resultado, totais[:, None], out=np.zeros_like(resultado), where=totais[:, None] > 0)


def coordenadas_completas(locais):
    """Local sem coordenada recebe a média das coordenadas da cidade; sem as duas, fica vazio."""
    medias = locais.groupby("cidade")[["latitude", "longitude"]].transform("mean")
    return locais[["latitude", "longitude"]].fillna(medias).to_numpy(dtype=float)


def distancias_entre_locais(locais):
    """Distâncias entre todos os locais, depois de completar as coordenadas."""
    coordenadas = coordenadas_completas(locais)
    return matriz_distancias_km(coordenadas[:, 0], coordenadas[:, 1])


def afinidade_distancia(treino, locais, usuarios, candidatos, tau, distancias=None):
    """Média, nos locais avaliados por cada usuário, de `exp(−km / τ)` até cada candidato."""
    usuarios = np.asarray(usuarios).astype(str)
    posicao_local = pd.Series(np.arange(len(locais)), index=locais["gmap_id"].to_numpy())
    posicao_usuario = pd.Series(np.arange(len(usuarios)), index=usuarios)
    if distancias is None:
        distancias = distancias_entre_locais(locais)
    proximidade = np.nan_to_num(np.exp(-distancias[:, posicao_local.reindex(candidatos).to_numpy()] / tau))

    do_treino = treino[treino["user_id"].isin(usuarios)]
    linhas = do_treino["user_id"].map(posicao_usuario).to_numpy()
    colunas = do_treino["gmap_id"].map(posicao_local).to_numpy()
    avaliados = sparse.csr_matrix((np.ones(len(linhas)), (linhas, colunas)), shape=(len(usuarios), len(locais)))
    totais = np.asarray(avaliados.sum(axis=1))
    somas = avaliados @ proximidade
    return np.divide(somas, totais, out=np.zeros_like(somas), where=totais > 0)


def pontuar(componentes, pesos):
    """`s(u, i) = α·sim + β·escore + γ·local + δ·pop`, com `pesos` na ordem (α, β, γ, δ)."""
    alfa, beta, gama, delta = pesos
    return (
        alfa * componentes["conteudo"]
        + beta * componentes["escore"][None, :]
        + gama * componentes["local"]
        + delta * componentes["popularidade"][None, :]
    )


def modelo_ponderado(componentes, pesos):
    """Devolve a função que o protocolo de avaliação recebe."""
    return lambda usuarios, candidatos: pontuar(componentes, pesos)


def grade_de_pesos(passo=0.1):
    """Todas as combinações de quatro pesos não negativos que somam 1."""
    partes = round(1 / passo)
    return [
        tuple(round(valor * passo, 10) for valor in (a, b, c, partes - a - b - c))
        for a in range(partes + 1)
        for b in range(partes + 1 - a)
        for c in range(partes + 1 - a - b)
    ]


def grade_ao_redor(pesos, raio=0.1, passo=0.05, alfa_minimo=0.1):
    """Combinações em torno de `pesos`, somando 1, para o refinamento."""
    return [
        combinacao
        for combinacao in grade_de_pesos(passo)
        if combinacao[0] >= alfa_minimo and all(abs(a - b) <= raio + 1e-9 for a, b in zip(combinacao, pesos))
    ]


def escolher_pesos(grade, limiar=0.95, alfa_minimo=0.1):
    """Entre as combinações com `alfa` mínimo e conversão ≥ limiar × a melhor, a de maior AUC de gosto."""
    elegiveis = grade[grade["alfa"] >= alfa_minimo - 1e-9]
    aptas = elegiveis[elegiveis["conversao"] >= limiar * elegiveis["conversao"].max()]
    return aptas.sort_values(["auc_gosto", "conversao"], ascending=False).iloc[0]


def escolher_variante(resultados, base, comparar, limiar=0.95):
    """Aplica o critério entre variantes; só troca a `base` se a AUC de gosto melhorar fora do empate."""
    conversao = {nome: resultado.por_usuario["conversao"].mean() for nome, resultado in resultados.items()}
    gosto = {nome: resultado.por_usuario["auc_gosto"].mean() for nome, resultado in resultados.items()}
    aptas = [nome for nome, valor in conversao.items() if valor >= limiar * max(conversao.values())]
    vencedora = max(aptas, key=gosto.get)
    if vencedora != base and base in aptas and comparar(resultados[vencedora], resultados[base], "auc_gosto")["empate"]:
        return base
    return vencedora


def ajustar_vies_usuarios(treino, escores, reg=REGULARIZACAO_VIES):
    """Viés regularizado de cada usuário em relação ao escore dos locais que avaliou."""
    residuos = treino["rating"] - treino["gmap_id"].map(escores)
    agrupado = residuos.groupby(treino["user_id"]).agg(["sum", "size"])
    return agrupado["sum"] / (agrupado["size"] + reg)


def prever_nota(usuarios, gmap_ids, escores, vies_usuario):
    """Escore do local + viés do usuário, limitado a [1, 5]; sem histórico, só o escore."""
    usuarios, gmap_ids = pd.Series(usuarios), pd.Series(gmap_ids)
    previsao = gmap_ids.map(escores) + usuarios.map(vies_usuario).fillna(0)
    return previsao.clip(1, 5).to_numpy()


def _coluna(tabela, nome):
    """Valores de uma coluna opcional, ou `None` em todas as linhas se ela não existir."""
    return list(tabela[nome]) if nome in tabela.columns else [None] * len(tabela)


def _locais(quantidade):
    return f"{quantidade} local" if quantidade == 1 else f"{quantidade} locais"


def _lista_de_textos(valores):
    if isinstance(valores, (list, tuple, np.ndarray)):
        return [valor for valor in valores if isinstance(valor, str)]
    return []


def _km_ate_ponto(latitude, longitude, latitudes, longitudes):
    """Distância de haversine de um ponto até vários pontos."""
    lat1, lon1 = np.radians(latitude), np.radians(longitude)
    lat2, lon2 = np.radians(latitudes), np.radians(longitudes)
    termo = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(termo, 0, 1)))


class Recomendador:
    """Modelo de conteúdo e escores de produto, com os três cenários do trabalho.

    Os pesos seguem a ordem (conteúdo, escore, local, popularidade). `pesos_usuario_novo` e
    `pesos_local_novo` (conteúdo, local) vêm das seções 3.5 e 3.6 do planejamento. No cenário 3,
    o conteúdo usa o perfil centrado em `centro_local_novo`, e a lista do usuário antigo reserva
    `cota_novos` posições a locais novos (abertos e sem avaliações no treino). No usuário novo, o peso do conteúdo vale para tudo o que é declarado:
    categorias, atributos e local de exemplo.
    """

    def __init__(
        self,
        pesos=PESOS_CONGELADOS,
        percentil=25,
        centro="usuario",
        local="distancia",
        tau=200,
        opcoes_vetor=None,
        pesos_usuario_novo=PESOS_USUARIO_NOVO,
        pesos_local_novo=(0.5, 0.5),
        centro_local_novo="fixo",
        cota_novos=1,
    ):
        if local not in {"cidade", "distancia", "media"}:
            raise ValueError(f"Local desconhecido: {local}")
        self.pesos = pesos
        self.percentil = percentil
        self.centro = centro
        self.local = local
        self.tau = tau
        self.opcoes_vetor = opcoes_vetor or {}
        self.pesos_usuario_novo = pesos_usuario_novo
        self.pesos_local_novo = pesos_local_novo
        self.centro_local_novo = centro_local_novo
        self.cota_novos = cota_novos

    def ajustar(self, treino, locais, vetorizador=None, matriz=None):
        """Ajusta com as avaliações do treino; sem vetorizador, ajusta um só com os locais do treino."""
        self.treino = treino[["user_id", "gmap_id", "rating"]].reset_index(drop=True)
        self.locais = locais.reset_index(drop=True)
        self._posicao_local = pd.Series(np.arange(len(self.locais)), index=self.locais["gmap_id"].to_numpy())
        if vetorizador is None:
            vetorizador = VetorizadorConteudo(**self.opcoes_vetor)
            vetorizador.fit(self.locais[self.locais["gmap_id"].isin(self.treino["gmap_id"])])
        self.vetorizador = vetorizador
        self.matriz = vetorizador.transform(self.locais) if matriz is None else matriz
        self.nomes_tokens = vetorizador.nomes_features()

        self.escores, self.parametros = escores_de_produto(self.treino, self.locais, self.percentil)
        self.perfis, usuarios = perfis_de_usuarios(self.treino, self.matriz, self._posicao_local.to_dict(), self.centro)
        self._linha_perfil = pd.Series(np.arange(len(usuarios)), index=usuarios)
        self.perfis_local_novo = self.perfis
        if self.centro_local_novo != self.centro:
            self.perfis_local_novo, usuarios_c3 = perfis_de_usuarios(
                self.treino, self.matriz, self._posicao_local.to_dict(), self.centro_local_novo
            )
            assert np.array_equal(usuarios, usuarios_c3)
        self.avaliacoes_por_usuario = self.treino.groupby("user_id").size()
        self.vies_usuario = ajustar_vies_usuarios(self.treino, self.escores["escore"])
        self.candidatos_padrao = self.escores.index[self.escores["aberto"] & (self.escores["avaliacoes"] > 0)].to_numpy().astype(str)
        self.locais_novos = self.escores.index[self.escores["aberto"] & (self.escores["avaliacoes"] == 0)].to_numpy().astype(str)
        self._distancias = None
        return self

    @property
    def distancias(self):
        if self._distancias is None:
            self._distancias = distancias_entre_locais(self.locais)
        return self._distancias

    def _afinidade(self, usuarios, candidatos):
        if self.local == "cidade":
            return afinidade_cidade(self.treino, self.locais, usuarios, candidatos)
        por_distancia = afinidade_distancia(self.treino, self.locais, usuarios, candidatos, self.tau, self.distancias)
        if self.local == "distancia":
            return por_distancia
        return (afinidade_cidade(self.treino, self.locais, usuarios, candidatos) + por_distancia) / 2

    def _similaridade(self, usuarios, vetores, perfis=None):
        perfis = self.perfis if perfis is None else perfis
        linhas = self._linha_perfil.reindex(usuarios)
        tem_perfil = linhas.notna().to_numpy()
        resultado = np.full((len(usuarios), vetores.shape[0]), 0.5)
        resultado[tem_perfil] = similaridade_conteudo(perfis[linhas[tem_perfil].astype(int).to_numpy()], vetores)
        return resultado

    def componentes(self, usuarios, candidatos):
        """Os quatro componentes, em lote; usuário sem perfil fica com a similaridade neutra de 0,5."""
        usuarios = np.asarray(usuarios).astype(str)
        colunas = self._posicao_local.reindex(candidatos).to_numpy()
        return {
            "conteudo": self._similaridade(usuarios, self.matriz[colunas]),
            "escore": self.escores["escore_normalizado"].reindex(candidatos).to_numpy(),
            "local": self._afinidade(usuarios, candidatos),
            "popularidade": self.escores["popularidade"].reindex(candidatos).to_numpy(),
        }

    def componentes_local_novo(self, usuarios, candidatos):
        """Conteúdo e local do cenário 3, em lote; o conteúdo usa o perfil com `centro_local_novo`.

        O perfil centrado em 3 descreve o tipo de lugar que a pessoa frequenta, o que prevê aonde ela
        vai; o centrado na média dela descreve do que ela gosta mais, o que serve ao cenário 1.
        """
        usuarios = np.asarray(usuarios).astype(str)
        colunas = self._posicao_local.reindex(candidatos).to_numpy()
        return {
            "conteudo": self._similaridade(usuarios, self.matriz[colunas], self.perfis_local_novo),
            "local": self._afinidade(usuarios, candidatos),
        }

    def pontuar(self, usuarios, candidatos):
        """Pontuação de cada usuário para cada candidato, em lote."""
        return pontuar(self.componentes(usuarios, candidatos), self.pesos)

    def prever_nota(self, usuarios, gmap_ids):
        return prever_nota(usuarios, gmap_ids, self.escores["escore"], self.vies_usuario)

    def _exigir_usuario(self, usuario):
        if usuario not in self._linha_perfil.index:
            raise ValueError(f"Usuário sem histórico no treino: {usuario}")

    def _tokens_que_mais_pesam(self, vetor_perfil, vetor_local, quantidade=3):
        """Tokens traduzidos com maior contribuição positiva para a similaridade."""
        contribuicao = np.asarray(vetor_perfil.multiply(vetor_local).todense()).ravel()
        tokens = []
        for indice in np.argsort(-contribuicao, kind="stable"):
            if contribuicao[indice] <= 0 or len(tokens) == quantidade:
                break
            traducao = traduzir_token(self.nomes_tokens[indice])
            if traducao is not None:
                tokens.append(traducao)
        return tokens

    def explicar(self, usuario, gmap_id):
        """Local bem avaliado pelo usuário mais parecido com o candidato e os tokens que mais pesam."""
        self._exigir_usuario(usuario)
        historico = self.treino[self.treino["user_id"] == usuario]
        vetor_local = self.matriz[self._posicao_local[gmap_id]]
        bons = historico[eh_relevante(historico["rating"]) & (historico["gmap_id"] != gmap_id)]
        parecido = None
        if len(bons):
            linhas = self._posicao_local.reindex(bons["gmap_id"]).to_numpy()
            similaridades = np.asarray((self.matriz[linhas] @ vetor_local.T).todense()).ravel()
            melhor = int(np.argmax(similaridades))
            if similaridades[melhor] > 0:
                parecido = {
                    "gmap_id": bons["gmap_id"].iloc[melhor],
                    "nome": self.locais["name"].iloc[linhas[melhor]],
                    "nota": int(bons["rating"].iloc[melhor]),
                    "similaridade": float(similaridades[melhor]),
                }
        tokens = self._tokens_que_mais_pesam(self.perfis[self._linha_perfil[usuario]], vetor_local)
        if parecido is not None:
            frase = f"Porque você gostou de {parecido['nome']} (nota {parecido['nota']})."
        else:
            frase = "Pela qualidade, pela proximidade e pela popularidade do local."
        if tokens:
            frase += f" Em comum com seu perfil: {', '.join(tokens)}."
        return {"parecido": parecido, "tokens": tokens, "frase": frase}

    def _tabela_de_lista(self, candidatos, ordem, pontuacoes, componentes):
        selecionados = candidatos[ordem]
        linhas = self._posicao_local.reindex(selecionados).to_numpy()
        return pd.DataFrame(
            {
                "gmap_id": selecionados,
                "nome": self.locais["name"].to_numpy()[linhas],
                "cidade": self.locais["cidade"].to_numpy()[linhas],
                "categoria_principal": self.locais["categoria_principal"].to_numpy()[linhas],
                "pontuacao": pontuacoes[ordem],
                "conteudo": componentes["conteudo"][ordem],
                "escore": componentes["escore"][ordem],
                "local": componentes["local"][ordem],
                "popularidade": componentes["popularidade"][ordem],
            }
        )

    def recomendar(self, usuario, n=10, com_explicacao=True, cota_novos=None):
        """Lista para um usuário com histórico, inclusive com 1 ou 2 avaliações: abertos não avaliados.

        Os locais novos concorrem com os demais e, se nenhum entrar no top-n, os `cota_novos` mais bem
        pontuados tomam as últimas posições. A coluna `novo` marca esses locais.
        """
        self._exigir_usuario(usuario)
        cota = self.cota_novos if cota_novos is None else cota_novos
        avaliados = set(self.treino.loc[self.treino["user_id"] == usuario, "gmap_id"])
        disponiveis = np.concatenate([self.candidatos_padrao, self.locais_novos]) if cota else self.candidatos_padrao
        candidatos = np.array([gmap_id for gmap_id in disponiveis if gmap_id not in avaliados])
        componentes = self.componentes([usuario], candidatos)
        pontuacoes = pontuar(componentes, self.pesos)[0]
        eh_novo = np.isin(candidatos, self.locais_novos)
        chave = pontuacoes
        if cota:
            chave = aplicar_cota_de_novos(pontuacoes[None, :], eh_novo, sparse.csr_matrix((1, len(candidatos))), n=n, cota=cota)[0]
        por_candidato = {
            "conteudo": componentes["conteudo"][0],
            "escore": componentes["escore"],
            "local": componentes["local"][0],
            "popularidade": componentes["popularidade"],
        }
        ordem = np.argsort(-chave, kind="stable")[:n]
        tabela = self._tabela_de_lista(candidatos, ordem, pontuacoes, por_candidato)
        tabela["novo"] = eh_novo[ordem]
        if com_explicacao:
            tabela["explicacao"] = [self.explicar(usuario, gmap_id)["frase"] for gmap_id in tabela["gmap_id"]]
        return tabela

    def _coordenadas(self):
        return coordenadas_completas(self.locais)

    def _centro_da_cidade(self, cidade):
        coordenadas = self._coordenadas()[(self.locais["cidade"] == cidade).to_numpy()]
        if len(coordenadas) == 0:
            raise ValueError(f"Cidade sem locais: {cidade}")
        return np.nanmean(coordenadas, axis=0)

    def _afinidade_declarada(self, cidade, candidatos):
        """Local para quem não tem histórico: mesma cidade, ou proximidade do centro da cidade informada."""
        if cidade is None:
            return np.zeros(len(candidatos))
        latitude, longitude = self._centro_da_cidade(cidade)
        linhas = self._posicao_local.reindex(candidatos).to_numpy()
        na_cidade = (self.locais["cidade"].to_numpy()[linhas] == cidade).astype(float)
        coordenadas = self._coordenadas()[linhas]
        proximidade = np.nan_to_num(np.exp(-_km_ate_ponto(latitude, longitude, coordenadas[:, 0], coordenadas[:, 1]) / self.tau))
        if self.local == "cidade":
            return na_cidade
        return proximidade if self.local == "distancia" else (na_cidade + proximidade) / 2

    def _vetores_declarados(self, cadastros):
        """Vetor de conteúdo de cada cadastro: categorias e atributos declarados mais o local de exemplo.

        As partes são somadas e normalizadas; cadastro sem nada declarado fica com vetor nulo, que dá a
        similaridade neutra de 0,5.
        """
        categorias, atributos = _coluna(cadastros, "categorias"), _coluna(cadastros, "atributos")
        declarados = [
            {"category": categoria, "MISC": atributo if isinstance(atributo, dict) else {}}
            for categoria, atributo in zip(categorias, atributos)
        ]
        vetores = self.vetorizador.transform(declarados)
        exemplos = _coluna(cadastros, "local_exemplo")
        com_exemplo = [i for i, exemplo in enumerate(exemplos) if isinstance(exemplo, str)]
        if com_exemplo:
            desconhecidos = {exemplos[i] for i in com_exemplo} - set(self._posicao_local.index)
            if desconhecidos:
                raise ValueError(f"Local de exemplo desconhecido: {sorted(desconhecidos)[0]}")
            linhas = self._posicao_local.reindex([exemplos[i] for i in com_exemplo]).to_numpy()
            seletor = sparse.csr_matrix(
                (np.ones(len(com_exemplo)), (com_exemplo, linhas)), shape=(len(declarados), len(self.locais))
            )
            vetores = vetores + seletor @ self.matriz
        return normalize(sparse.csr_matrix(vetores), norm="l2")

    def _afinidades_declaradas(self, cidades, candidatos):
        """Local de cada cadastro pela cidade informada; sem cidade, 0."""
        resultado = np.zeros((len(cidades), len(candidatos)))
        por_cidade = {}
        for i, cidade in enumerate(cidades):
            if isinstance(cidade, str):
                por_cidade.setdefault(cidade, []).append(i)
        for cidade, linhas in por_cidade.items():
            resultado[linhas] = self._afinidade_declarada(cidade, candidatos)
        return resultado

    def componentes_cadastros(self, cadastros, candidatos):
        """Os quatro componentes, em lote, para quem não tem histórico, com o que cada cadastro informa.

        `cadastros` tem uma linha por pessoa e, todas opcionais, as colunas `cidade`, `categorias`
        (lista), `atributos` (grupo -> lista de valores) e `local_exemplo` (`gmap_id`).
        """
        candidatos = np.asarray(candidatos).astype(str)
        colunas = self._posicao_local.reindex(candidatos).to_numpy()
        return {
            "conteudo": similaridade_conteudo(self._vetores_declarados(cadastros), self.matriz[colunas]),
            "escore": self.escores["escore_normalizado"].reindex(candidatos).to_numpy(),
            "local": self._afinidades_declaradas(_coluna(cadastros, "cidade"), candidatos),
            "popularidade": self.escores["popularidade"].reindex(candidatos).to_numpy(),
        }

    def coincidencia_de_categorias(self, cadastros, candidatos):
        """Matriz cadastros × candidatos com 1 onde o candidato tem alguma das categorias declaradas."""
        linhas = self._posicao_local.reindex(np.asarray(candidatos).astype(str)).to_numpy()
        do_candidato = [set(_lista_de_textos(valor)) for valor in self.locais["category"].to_numpy()[linhas]]
        declaradas = [set(_lista_de_textos(valor)) for valor in _coluna(cadastros, "categorias")]
        vocabulario = {categoria: i for i, categoria in enumerate(sorted(set().union(*do_candidato, *declaradas)))}

        def incidencia(conjuntos):
            pares = [(i, vocabulario[categoria]) for i, conjunto in enumerate(conjuntos) for categoria in conjunto]
            linhas_, colunas_ = zip(*pares) if pares else ((), ())
            return sparse.csr_matrix((np.ones(len(pares)), (linhas_, colunas_)), shape=(len(conjuntos), len(vocabulario)))

        return (np.asarray((incidencia(declaradas) @ incidencia(do_candidato).T).todense()) > 0).astype(float)

    def recomendar_usuario_novo(
        self, cidade=None, categorias=None, atributos=None, local_exemplo=None, preco=None, n=10, filtrar_categorias=False
    ):
        """Lista para quem não tem histórico, com o que a pessoa informar; tudo é opcional.

        Regra de não esvaziar: preferências e filtros nunca deixam a lista vazia. Com `filtrar_categorias`,
        os locais das categorias declaradas vêm primeiro e os demais completam a lista. O filtro de preço
        (nível de 1 a 4) é ignorado se sobrarem menos locais que o pedido. Os avisos ficam em
        `tabela.attrs["avisos"]`.
        """
        avisos = []
        candidatos = np.array([gmap_id for gmap_id in self.candidatos_padrao if gmap_id != local_exemplo])
        if preco is not None:
            niveis = self.locais["preco_nivel"].to_numpy()[self._posicao_local.reindex(candidatos).to_numpy()]
            com_preco = niveis == preco
            if com_preco.sum() >= n:
                candidatos = candidatos[com_preco]
            else:
                avisos.append(f"Há só {_locais(int(com_preco.sum()))} com esse preço; o filtro de preço foi ignorado.")
        cadastro = pd.DataFrame(
            {"cidade": [cidade], "categorias": [categorias], "atributos": [atributos], "local_exemplo": [local_exemplo]}
        )
        componentes = self.componentes_cadastros(cadastro, candidatos)
        pontuacoes = pontuar(componentes, self.pesos_usuario_novo)[0]
        chave = pontuacoes
        if filtrar_categorias and categorias:
            coincide = self.coincidencia_de_categorias(cadastro, candidatos)[0]
            chave = pontuacoes + coincide
            if coincide.sum() < n:
                avisos.append(f"Há só {_locais(int(coincide.sum()))} das categorias escolhidas; a lista foi completada com outros.")
        if cidade is not None:
            na_cidade = int((self.locais["cidade"].to_numpy()[self._posicao_local.reindex(candidatos).to_numpy()] == cidade).sum())
            if na_cidade < n:
                avisos.append(f"{cidade} tem só {_locais(na_cidade)} disponíveis; a lista foi ampliada para os mais próximos.")
        por_candidato = {
            "conteudo": componentes["conteudo"][0],
            "escore": componentes["escore"],
            "local": componentes["local"][0],
            "popularidade": componentes["popularidade"],
        }
        ordem = np.argsort(-chave, kind="stable")[:n]
        tabela = self._tabela_de_lista(candidatos, ordem, pontuacoes, por_candidato)
        tabela.attrs["avisos"] = avisos
        return tabela

    def _ponto_do_cadastro(self, cadastro):
        latitude, longitude = cadastro.get("latitude"), cadastro.get("longitude")
        if latitude is not None and longitude is not None and np.isfinite(latitude) and np.isfinite(longitude):
            return float(latitude), float(longitude)
        cidade = cadastro.get("cidade")
        if isinstance(cidade, str) and (self.locais["cidade"] == cidade).any():
            return tuple(self._centro_da_cidade(cidade))
        return None

    def _afinidade_local_novo(self, usuarios, cadastro):
        """Afinidade de cada usuário com um local que não está nas avaliações."""
        do_treino = self.treino[self.treino["user_id"].isin(usuarios)]
        posicao_usuario = pd.Series(np.arange(len(usuarios)), index=usuarios)
        avaliados = sparse.csr_matrix(
            (
                np.ones(len(do_treino)),
                (do_treino["user_id"].map(posicao_usuario).to_numpy(), do_treino["gmap_id"].map(self._posicao_local).to_numpy()),
            ),
            shape=(len(usuarios), len(self.locais)),
        )
        totais = np.asarray(avaliados.sum(axis=1)).ravel()
        na_cidade = (self.locais["cidade"] == cadastro.get("cidade")).to_numpy(dtype=float)
        por_cidade = avaliados @ na_cidade
        ponto = self._ponto_do_cadastro(cadastro)
        por_distancia = np.zeros(len(usuarios))
        if ponto is not None:
            coordenadas = self._coordenadas()
            proximidade = np.nan_to_num(np.exp(-_km_ate_ponto(*ponto, coordenadas[:, 0], coordenadas[:, 1]) / self.tau))
            por_distancia = avaliados @ proximidade
        soma = {"cidade": por_cidade, "distancia": por_distancia, "media": (por_cidade + por_distancia) / 2}[self.local]
        return np.divide(soma, totais, out=np.zeros_like(soma, dtype=float), where=totais > 0)

    def usuarios_para_local_novo(self, cadastro, n=10, minimo_avaliacoes=MINIMO_USUARIO_ANTIGO):
        """Usuários antigos mais indicados para um local novo, vindo da tabela ou de um cadastro manual."""
        usuarios = self.avaliacoes_por_usuario.index[self.avaliacoes_por_usuario >= minimo_avaliacoes].to_numpy().astype(str)
        vetor = self.vetorizador.transform([cadastro])
        conteudo = self._similaridade(usuarios, vetor, self.perfis_local_novo)[:, 0]
        local = self._afinidade_local_novo(usuarios, cadastro)
        alfa, gama = self.pesos_local_novo
        pontuacoes = alfa * conteudo + gama * local
        ordem = np.argsort(-pontuacoes, kind="stable")[:n]
        return pd.DataFrame(
            {"user_id": usuarios[ordem], "pontuacao": pontuacoes[ordem], "conteudo": conteudo[ordem], "local": local[ordem]}
        )

    def _popularidade_de_local_novo(self, cidade):
        avaliados = self.escores[self.escores["avaliacoes"] > 0]
        da_cidade = avaliados.loc[avaliados["cidade"] == cidade, "popularidade"]
        return float(da_cidade.median() if len(da_cidade) else avaliados["popularidade"].median())

    def posicao_local_novo(self, usuario, cadastro, n=10):
        """Posição de um local novo entre os candidatos do usuário e a decisão de recomendá-lo."""
        self._exigir_usuario(usuario)
        usuarios = np.array([usuario])
        alfa, beta, gama, delta = self.pesos
        escore_novo = (self.parametros["C"] - 1) / 4
        pontuacao = (
            alfa * self._similaridade(usuarios, self.vetorizador.transform([cadastro]))[0, 0]
            + beta * escore_novo
            + gama * self._afinidade_local_novo(usuarios, cadastro)[0]
            + delta * self._popularidade_de_local_novo(cadastro.get("cidade"))
        )
        avaliados = set(self.treino.loc[self.treino["user_id"] == usuario, "gmap_id"])
        candidatos = np.array([gmap_id for gmap_id in self.candidatos_padrao if gmap_id not in avaliados])
        demais = self.pontuar(usuarios, candidatos)[0]
        posicao = int((demais > pontuacao).sum()) + 1
        return {"posicao": posicao, "total": len(candidatos) + 1, "recomendar": posicao <= n, "pontuacao": float(pontuacao)}


def calcular_componentes(treino, locais, usuarios, candidatos, percentil=PERCENTIL_PADRAO, centro="fixo", local="cidade", tau=None, opcoes_vetor=None):
    """Calcula os quatro componentes para usuários e candidatos, olhando só o treino."""
    modelo = Recomendador(percentil=percentil, centro=centro, local=local, tau=tau, opcoes_vetor=opcoes_vetor)
    return modelo.ajustar(treino, locais).componentes(usuarios, candidatos)
