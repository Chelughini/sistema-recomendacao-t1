"""Divisão temporal das avaliações e conjuntos de cada cenário."""

import numpy as np
import pandas as pd

LIMIAR_RELEVANCIA = 4
MINIMO_USUARIO_ANTIGO = 3


def eh_relevante(notas):
    """Uma avaliação é relevante, ou convertida, quando a nota é 4 ou maior."""
    return notas >= LIMIAR_RELEVANCIA


def calcular_cortes(avaliacoes):
    """Devolve o corte de teste (quantil 80% das datas) e o de validação (exatamente um ano antes)."""
    corte_teste = avaliacoes["data"].quantile(0.8)
    return corte_teste, corte_teste - pd.DateOffset(years=1)


def dividir_temporal(avaliacoes):
    """Separa as partições; cada corte pertence ao período que começa nele."""
    corte_teste, corte_validacao = calcular_cortes(avaliacoes)
    datas = avaliacoes["data"]
    return {
        "treino": avaliacoes[datas < corte_validacao],
        "validacao": avaliacoes[(datas >= corte_validacao) & (datas < corte_teste)],
        "treino_total": avaliacoes[datas < corte_teste],
        "teste": avaliacoes[datas >= corte_teste],
    }


def segmentar(alvo, treino, sufixo=""):
    """Classifica cada avaliação do alvo conforme o histórico do usuário no treino correspondente."""
    historico = alvo["user_id"].map(treino.groupby("user_id").size()).fillna(0).astype(int)
    segmento = np.select(
        [historico == 0, historico < MINIMO_USUARIO_ANTIGO], ["novo", "intermediario"], default="antigo"
    )
    return alvo.assign(**{f"avaliacoes_no_treino{sufixo}": historico, f"segmento{sufixo}": segmento})


def locais_novos_naturais(alvo, treino):
    """Locais cuja primeira avaliação está no período-alvo, em ordem fixa."""
    return np.sort(np.setdiff1d(alvo["gmap_id"].unique().astype(str), treino["gmap_id"].unique().astype(str)))


def sortear_locais_simulados(treino, locais, quantidade=100, minimo_avaliacoes=20, excluir=(), semente=42):
    """Sorteia, olhando só o treino, locais abertos para simular um local novo."""
    contagem = treino.groupby("gmap_id").size()
    abertos = locais.loc[~(locais["fechado_perm"] | locais["fechado_temp"]), "gmap_id"]
    elegiveis = contagem[contagem >= minimo_avaliacoes].index.intersection(abertos).difference(pd.Index(excluir))
    gerador = np.random.default_rng(semente)
    return np.sort(gerador.choice(np.sort(elegiveis.to_numpy().astype(str)), size=quantidade, replace=False))


def retirar_locais(treino, gmap_ids):
    """Remove do treino as avaliações dos locais simulados como novos."""
    return treino[~treino["gmap_id"].isin(gmap_ids)]


def simular_cadastros(alvo, locais, segmento="novo", coluna_segmento="segmento", minimo_avaliacoes=2):
    """Simula o cadastro dos usuários novos: a primeira avaliação no período-alvo vira o que a pessoa informa.

    Ficam os usuários do segmento com `minimo_avaliacoes` ou mais avaliações no alvo. Em ordem de data
    (e de `gmap_id`, para desempatar), a primeira dá a cidade, a categoria principal e o local de exemplo;
    as demais são o que se tenta acertar. Devolve um cadastro por usuário, indexado por `user_id`, e os
    pares (user_id, gmap_id) do cadastro, que saem do alvo e da lista.
    """
    do_segmento = alvo[alvo[coluna_segmento] == segmento]
    contagem = do_segmento.groupby("user_id").size()
    elegiveis = do_segmento[do_segmento["user_id"].isin(contagem.index[contagem >= minimo_avaliacoes])]
    primeiras = elegiveis.sort_values(["user_id", "data", "gmap_id"], kind="stable").drop_duplicates("user_id")
    dados_do_local = locais.set_index("gmap_id")[["cidade", "categoria_principal"]]
    cadastros = primeiras[["user_id", "gmap_id"]].join(dados_do_local, on="gmap_id")
    cadastros = cadastros.rename(columns={"gmap_id": "local_exemplo"})
    cadastros["categorias"] = [[categoria] if isinstance(categoria, str) else [] for categoria in cadastros["categoria_principal"]]
    pares = primeiras[["user_id", "gmap_id"]].reset_index(drop=True)
    return cadastros.drop(columns="categoria_principal").set_index("user_id"), pares


def montar_conjuntos(avaliacoes, locais, quantidade=100, minimo_avaliacoes=20, semente=42):
    """Monta as partições, os treinos do cenário 3, os segmentos e a lista de locais novos."""
    particoes = dividir_temporal(avaliacoes)
    simulados_validacao = sortear_locais_simulados(
        particoes["treino"], locais, quantidade, minimo_avaliacoes, semente=semente
    )
    simulados_teste = sortear_locais_simulados(
        particoes["treino_total"], locais, quantidade, minimo_avaliacoes, excluir=simulados_validacao, semente=semente
    )
    treino_c3 = retirar_locais(particoes["treino"], simulados_validacao)
    treino_total_c3 = retirar_locais(particoes["treino_total"], simulados_teste)
    validacao = segmentar(segmentar(particoes["validacao"], particoes["treino"]), treino_c3, "_c3")
    teste = segmentar(segmentar(particoes["teste"], particoes["treino_total"]), treino_total_c3, "_c3")

    grupos = [
        (locais_novos_naturais(particoes["validacao"], particoes["treino"]), "natural", "validacao"),
        (simulados_validacao, "simulado", "validacao"),
        (locais_novos_naturais(particoes["teste"], particoes["treino_total"]), "natural", "teste"),
        (simulados_teste, "simulado", "teste"),
    ]
    locais_novos = pd.concat(
        [pd.DataFrame({"gmap_id": ids, "origem": origem, "conjunto": conjunto}) for ids, origem, conjunto in grupos],
        ignore_index=True,
    )
    return {
        "treino": particoes["treino"],
        "validacao": validacao,
        "treino_total": particoes["treino_total"],
        "teste": teste,
        "treino_c3": treino_c3,
        "treino_total_c3": treino_total_c3,
        "locais_novos": locais_novos,
    }
