"""Métricas vistas em aula e protocolo único de avaliação dos modelos."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import kendalltau, rankdata, spearmanr

from src.analises import erros_de_nota, ic_bootstrap
from src.divisao import eh_relevante

__all__ = [
    "ProtocoloAvaliacao",
    "ResultadoAvaliacao",
    "auc",
    "avaliar",
    "comparar",
    "correlacao_rankings",
    "curva_roc",
    "curva_roc_media",
    "erros_de_nota",
    "ic_bootstrap",
    "intervalo",
    "montar_protocolo",
]

MINIMO_PONTUAVEIS = 10
MINIMO_CORRELACAO = 3
AMPLITUDE_DESEMPATE = 1e-9


def auc(positivos, negativos):
    """Área sob a curva ROC: chance de um positivo ficar acima de um negativo; empate vale meio."""
    positivos, negativos = np.asarray(positivos, dtype=float), np.asarray(negativos, dtype=float)
    if len(positivos) == 0 or len(negativos) == 0:
        return np.nan
    postos = rankdata(np.concatenate([positivos, negativos]))
    soma = postos[: len(positivos)].sum()
    return (soma - len(positivos) * (len(positivos) + 1) / 2) / (len(positivos) * len(negativos))


def curva_roc(rotulos, pontuacoes):
    """Pontos da curva ROC (falsos positivos, verdadeiros positivos), um a cada valor distinto de pontuação."""
    rotulos, pontuacoes = np.asarray(rotulos, dtype=bool), np.asarray(pontuacoes, dtype=float)
    ordem = np.argsort(-pontuacoes, kind="stable")
    rotulos, pontuacoes = rotulos[ordem], pontuacoes[ordem]
    limites = np.r_[np.flatnonzero(np.diff(pontuacoes)), len(pontuacoes) - 1]
    verdadeiros = np.cumsum(rotulos)[limites]
    falsos = np.cumsum(~rotulos)[limites]
    return np.r_[0.0, falsos / max(falsos[-1], 1)], np.r_[0.0, verdadeiros / max(verdadeiros[-1], 1)]


def curva_roc_media(pares, pontos=101):
    """Curva ROC média entre usuários, interpolada em uma grade de falsos positivos."""
    grade = np.linspace(0, 1, pontos)
    curvas = [np.interp(grade, *curva_roc(rotulos, valores)) for rotulos, valores in pares]
    return grade, np.mean(curvas, axis=0)


def correlacao_rankings(pontuacoes, notas):
    """Spearman e tau-b de Kendall; devolve NaN se faltam avaliações ou não há variação."""
    pontuacoes, notas = np.asarray(pontuacoes, dtype=float), np.asarray(notas, dtype=float)
    if len(notas) < MINIMO_CORRELACAO or np.ptp(notas) == 0 or np.ptp(pontuacoes) == 0:
        return np.nan, np.nan
    return spearmanr(pontuacoes, notas).statistic, kendalltau(pontuacoes, notas, variant="b").statistic


@dataclass
class ProtocoloAvaliacao:
    """Os mesmos usuários, candidatos e conversões para todo modelo."""

    usuarios: np.ndarray
    candidatos: np.ndarray
    notas: sparse.csr_matrix
    ja_avaliados: sparse.csr_matrix
    contagem_treino: np.ndarray
    total_treino: int


@dataclass
class ResultadoAvaliacao:
    """Valores por usuário, para os intervalos de confiança, e medidas do modelo inteiro."""

    por_usuario: pd.DataFrame
    listas: np.ndarray
    cobertura_catalogo: float
    cobertura_usuarios: float
    cobertura_itens: float

    def resumo(self):
        medias = self.por_usuario.mean()
        coberturas = pd.Series(
            {
                "cobertura_catalogo": self.cobertura_catalogo,
                "cobertura_usuarios": self.cobertura_usuarios,
                "cobertura_itens": self.cobertura_itens,
            }
        )
        return pd.concat([medias, coberturas])


def _matriz_esparsa(tabela, usuarios, candidatos, valores):
    posicao_usuario = pd.Series(np.arange(len(usuarios)), index=usuarios)
    posicao_candidato = pd.Series(np.arange(len(candidatos)), index=candidatos)
    linhas = tabela["user_id"].map(posicao_usuario)
    colunas = tabela["gmap_id"].map(posicao_candidato)
    presentes = (linhas.notna() & colunas.notna()).to_numpy()
    return sparse.csr_matrix(
        (np.asarray(valores, dtype=float)[presentes], (linhas[presentes].astype(int), colunas[presentes].astype(int))),
        shape=(len(usuarios), len(candidatos)),
    )


def montar_protocolo(
    treino,
    alvo,
    locais,
    segmentos,
    coluna_segmento="segmento",
    candidatos=None,
    pares_excluidos=None,
    maximo_usuarios=10_000,
    semente=42,
):
    """Monta o protocolo: candidatos, usuários com conversão e notas do período-alvo.

    Sem lista informada, os candidatos são os locais abertos presentes no treino. `pares_excluidos`
    traz pares (user_id, gmap_id) que saem da lista além dos avaliados no treino.
    """
    if candidatos is None:
        abertos = locais.loc[~(locais["fechado_perm"] | locais["fechado_temp"]), "gmap_id"]
        candidatos = np.intersect1d(treino["gmap_id"].unique().astype(str), abertos.to_numpy().astype(str))
    else:
        candidatos = np.sort(np.asarray(candidatos).astype(str))

    do_alvo = alvo[alvo[coluna_segmento].isin(list(segmentos)) & alvo["gmap_id"].isin(candidatos)]
    if pares_excluidos is not None:
        chaves = pd.MultiIndex.from_frame(pares_excluidos[["user_id", "gmap_id"]])
        do_alvo = do_alvo[~pd.MultiIndex.from_frame(do_alvo[["user_id", "gmap_id"]]).isin(chaves)]
    convertidas = do_alvo[eh_relevante(do_alvo["rating"])]
    usuarios = np.sort(convertidas["user_id"].unique().astype(str))
    if len(usuarios) > maximo_usuarios:
        usuarios = np.sort(np.random.default_rng(semente).choice(usuarios, size=maximo_usuarios, replace=False))

    excluidos = [treino[["user_id", "gmap_id"]]]
    if pares_excluidos is not None:
        excluidos.append(pares_excluidos[["user_id", "gmap_id"]])
    excluidos = pd.concat(excluidos, ignore_index=True)
    ja_avaliados = _matriz_esparsa(excluidos, usuarios, candidatos, np.ones(len(excluidos)))
    ja_avaliados.data[:] = 1
    notas = _matriz_esparsa(do_alvo, usuarios, candidatos, do_alvo["rating"].to_numpy())
    contagem = treino.groupby("gmap_id").size().reindex(candidatos, fill_value=0).to_numpy()
    return ProtocoloAvaliacao(usuarios, candidatos, notas, ja_avaliados, contagem, len(treino))


def _pontuacoes_validas(protocolo, modelo):
    pontuacoes = np.asarray(modelo(protocolo.usuarios, protocolo.candidatos), dtype=float)
    formato = (len(protocolo.usuarios), len(protocolo.candidatos))
    if pontuacoes.shape != formato:
        raise ValueError(f"O modelo devolveu {pontuacoes.shape}, e o esperado é {formato}.")
    return pontuacoes


def _montar_listas(pontuacoes, ja_avaliados, k, semente):
    """Top-k de cada usuário; -1 marca posições sem local disponível.

    Um ruído mínimo desfaz empates por sorteio, para não favorecer a ordem do catálogo.
    """
    chave = pontuacoes + AMPLITUDE_DESEMPATE * np.random.default_rng(semente).random(pontuacoes.shape)
    chave[np.isnan(pontuacoes)] = -np.inf
    linhas, colunas = ja_avaliados.nonzero()
    chave[linhas, colunas] = -np.inf
    tamanho = min(k, chave.shape[1])
    topo = np.argpartition(-chave, tamanho - 1, axis=1)[:, :tamanho]
    ordem = np.argsort(-np.take_along_axis(chave, topo, axis=1), axis=1)
    listas = np.take_along_axis(topo, ordem, axis=1)
    listas[np.take_along_axis(chave, listas, axis=1) == -np.inf] = -1
    return listas


def _fracao_na_lista(listas, marcados):
    validos = listas >= 0
    acertos = np.take_along_axis(marcados, np.where(validos, listas, 0), axis=1) & validos
    tamanhos = validos.sum(axis=1)
    return np.divide(acertos.sum(axis=1), tamanhos, out=np.full(len(listas), np.nan), where=tamanhos > 0), acertos


def _novidade(listas, contagem, total):
    autoinformacao = -np.log2(np.maximum(contagem, 1) / total)
    valores = np.where(listas >= 0, autoinformacao[np.where(listas >= 0, listas, 0)], np.nan)
    tem_itens = (listas >= 0).any(axis=1)
    resultado = np.full(len(listas), np.nan)
    resultado[tem_itens] = np.nanmean(valores[tem_itens], axis=1)
    return resultado


def _diversidade(listas, vetores):
    """Média de 1 − cosseno entre os pares da lista, com vetores de norma 1."""
    resultado = np.full(len(listas), np.nan)
    normas = np.asarray(vetores.multiply(vetores).sum(axis=1)).ravel()
    for i, lista in enumerate(listas):
        lista = lista[lista >= 0]
        if len(lista) < 2:
            continue
        soma = np.asarray(vetores[lista].sum(axis=0)).ravel()
        pares = (soma @ soma - normas[lista].sum()) / (len(lista) * (len(lista) - 1))
        resultado[i] = 1 - pares
    return resultado


def _por_usuario_em_listas_de_notas(protocolo, pontuacoes, com_correlacao):
    auc_gosto = np.full(len(protocolo.usuarios), np.nan)
    spearman = np.full(len(protocolo.usuarios), np.nan)
    kendall = np.full(len(protocolo.usuarios), np.nan)
    notas = protocolo.notas
    limpas = np.nan_to_num(pontuacoes, nan=-np.inf)
    for i in range(notas.shape[0]):
        colunas = notas.indices[notas.indptr[i] : notas.indptr[i + 1]]
        valores = notas.data[notas.indptr[i] : notas.indptr[i + 1]]
        relevantes = eh_relevante(valores)
        if relevantes.any() and (~relevantes).any():
            auc_gosto[i] = auc(limpas[i, colunas[relevantes]], limpas[i, colunas[~relevantes]])
        if com_correlacao:
            spearman[i], kendall[i] = correlacao_rankings(pontuacoes[i, colunas], valores)
    return auc_gosto, spearman, kendall


def _auc_consumo(protocolo, pontuacoes, convertidos):
    resultado = np.full(len(protocolo.usuarios), np.nan)
    limpas = np.nan_to_num(pontuacoes, nan=-np.inf)
    ja_avaliados = protocolo.ja_avaliados.toarray().astype(bool)
    for i in range(len(protocolo.usuarios)):
        positivos = convertidos[i]
        negativos = ~positivos & ~ja_avaliados[i]
        resultado[i] = auc(limpas[i, positivos], limpas[i, negativos])
    return resultado


def avaliar(
    protocolo,
    modelo,
    k=10,
    semente=42,
    completo=False,
    com_correlacao=False,
    vetores=None,
    modelo_obvio=None,
):
    """Avalia um modelo, que recebe (usuarios, candidatos) e devolve a matriz de pontuações.

    NaN na matriz marca um par que o modelo não consegue pontuar. Por padrão calcula só conversão,
    consumo e AUC de gosto, para a grade de pesos; `completo` acrescenta as demais métricas.
    """
    pontuacoes = _pontuacoes_validas(protocolo, modelo)
    listas = _montar_listas(pontuacoes, protocolo.ja_avaliados, k, semente)
    consumidos = protocolo.notas.toarray() > 0
    convertidos = eh_relevante(protocolo.notas.toarray())
    conversao, acertos = _fracao_na_lista(listas, convertidos)
    consumo, _ = _fracao_na_lista(listas, consumidos)
    auc_gosto, spearman, kendall = _por_usuario_em_listas_de_notas(protocolo, pontuacoes, com_correlacao)

    por_usuario = {"conversao": conversao, "consumo": consumo, "auc_gosto": auc_gosto}
    if com_correlacao:
        por_usuario["spearman"] = spearman
        por_usuario["kendall"] = kendall
    if completo:
        por_usuario["auc_consumo"] = _auc_consumo(protocolo, pontuacoes, convertidos)
        por_usuario["novidade"] = _novidade(listas, protocolo.contagem_treino, protocolo.total_treino)
        if vetores is not None:
            por_usuario["diversidade"] = _diversidade(listas, vetores)
        if modelo_obvio is not None:
            pontuacoes_obvias = _pontuacoes_validas(protocolo, modelo_obvio)
            obvias = _montar_listas(pontuacoes_obvias, protocolo.ja_avaliados, k, semente)
            na_lista_obvia = np.zeros_like(convertidos)
            usuarios_validos, posicoes_validas = np.nonzero(obvias >= 0)
            na_lista_obvia[usuarios_validos, obvias[usuarios_validos, posicoes_validas]] = True
            por_usuario["serendipidade"], _ = _fracao_na_lista(listas, convertidos & ~na_lista_obvia)

    pontuaveis = np.isfinite(pontuacoes)
    linhas, colunas = protocolo.ja_avaliados.nonzero()
    pontuaveis[linhas, colunas] = False
    return ResultadoAvaliacao(
        por_usuario=pd.DataFrame(por_usuario, index=pd.Index(protocolo.usuarios, name="user_id")),
        listas=listas,
        cobertura_catalogo=len(np.unique(listas[listas >= 0])) / len(protocolo.candidatos),
        cobertura_usuarios=float((pontuaveis.sum(axis=1) >= MINIMO_PONTUAVEIS).mean()),
        cobertura_itens=float((pontuaveis.sum(axis=0) >= MINIMO_PONTUAVEIS).mean()),
    )


def intervalo(resultado, metrica):
    """Média da métrica e intervalo de 95% por bootstrap de usuários."""
    return ic_bootstrap(resultado.por_usuario[metrica].dropna().to_numpy())


def comparar(resultado_a, resultado_b, metrica):
    """Diferença pareada por usuário (a − b), com intervalo de 95%; se ele inclui zero, é empate."""
    pares = pd.concat([resultado_a.por_usuario[metrica], resultado_b.por_usuario[metrica]], axis=1, keys=["a", "b"]).dropna()
    media, inferior, superior = ic_bootstrap((pares["a"] - pares["b"]).to_numpy())
    return {
        "diferenca": media,
        "inferior": inferior,
        "superior": superior,
        "empate": bool(inferior <= 0 <= superior),
        "usuarios": len(pares),
    }
