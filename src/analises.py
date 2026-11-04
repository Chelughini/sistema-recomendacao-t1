"""Cálculos das análises que orientam as decisões do trabalho."""

import numpy as np
import pandas as pd
from scipy import sparse


def k_core(avaliacoes, k):
    """Remove usuários e locais com menos de `k` avaliações até estabilizar."""
    atual = avaliacoes
    while True:
        tamanho = len(atual)
        for coluna in ["user_id", "gmap_id"]:
            contagem = atual.groupby(coluna)[coluna].transform("size")
            atual = atual[contagem >= k]
        if len(atual) == tamanho:
            return atual


def matriz_binaria(linhas, colunas):
    """Monta a matriz esparsa binária de presença a partir de pares (linha, coluna)."""
    codigos_linhas, _ = pd.factorize(np.asarray(linhas))
    codigos_colunas, _ = pd.factorize(np.asarray(colunas))
    forma = (codigos_linhas.max() + 1, codigos_colunas.max() + 1)
    valores = np.ones(len(codigos_linhas), dtype=np.int32)
    matriz = sparse.csr_matrix((valores, (codigos_linhas, codigos_colunas)), shape=forma)
    matriz.data[:] = 1
    return matriz


def suporte_vizinhos(matriz, linhas, minimos=(2, 3, 5, 10), posicao=20, lote=500):
    """Conta, para cada linha, os vizinhos com ao menos m itens em comum e o suporte do vizinho em `posicao`."""
    registros = []
    linhas = np.asarray(linhas)
    for inicio in range(0, len(linhas), lote):
        selecao = linhas[inicio : inicio + lote]
        comuns = (matriz[selecao] @ matriz.T).tocsr()
        for i, linha in enumerate(selecao):
            indices = comuns.indices[comuns.indptr[i] : comuns.indptr[i + 1]]
            valores = comuns.data[comuns.indptr[i] : comuns.indptr[i + 1]]
            valores = np.sort(valores[indices != linha])[::-1]
            registro = {f"vizinhos_{m}+": int((valores >= m).sum()) for m in minimos}
            registro["suporte_vizinho"] = int(valores[posicao - 1]) if len(valores) >= posicao else 0
            registros.append(registro)
    return pd.DataFrame(registros)


def decompor_variancia(tabela, iteracoes=50):
    """Mede quanto da variância da nota é explicado pelo local e por local + usuário."""
    notas = tabela["rating"].to_numpy(dtype=float)
    usuarios, _ = pd.factorize(tabela["user_id"])
    locais, _ = pd.factorize(tabela["gmap_id"])
    n, n_usuarios, n_locais = len(notas), usuarios.max() + 1, locais.max() + 1
    media = notas.mean()
    total = ((notas - media) ** 2).sum()

    def media_por_grupo(valores, grupos, tamanho):
        return np.bincount(grupos, valores, tamanho) / np.bincount(grupos, minlength=tamanho)

    efeito_local = media_por_grupo(notas - media, locais, n_locais)
    residuo_local = ((notas - media - efeito_local[locais]) ** 2).sum()

    efeito_usuario = np.zeros(n_usuarios)
    efeito_conjunto = efeito_local.copy()
    for _ in range(iteracoes):
        efeito_usuario = media_por_grupo(notas - media - efeito_conjunto[locais], usuarios, n_usuarios)
        efeito_conjunto = media_por_grupo(notas - media - efeito_usuario[usuarios], locais, n_locais)
    residuo_conjunto = ((notas - media - efeito_usuario[usuarios] - efeito_conjunto[locais]) ** 2).sum()

    def ajustado(residuo, parametros):
        return 1 - (residuo / max(n - parametros, 1)) / (total / (n - 1))

    return {
        "local": 1 - residuo_local / total,
        "local_ajustado": ajustado(residuo_local, n_locais),
        "local_usuario": 1 - residuo_conjunto / total,
        "local_usuario_ajustado": ajustado(residuo_conjunto, n_locais + n_usuarios - 1),
    }


def matriz_jaccard(listas_de_categorias):
    """Calcula o índice de Jaccard entre todos os pares de listas de categorias."""
    pares = [(i, categoria) for i, categorias in enumerate(listas_de_categorias) for categoria in set(categorias)]
    linhas = np.array([par[0] for par in pares])
    codigos, _ = pd.factorize(np.array([par[1] for par in pares]))
    forma = (len(listas_de_categorias), codigos.max() + 1)
    presenca = sparse.csr_matrix((np.ones(len(linhas), dtype=np.int32), (linhas, codigos)), shape=forma)
    comuns = (presenca @ presenca.T).toarray()
    tamanhos = np.diag(comuns)
    uniao = tamanhos[:, None] + tamanhos[None, :] - comuns
    return np.divide(comuns, uniao, out=np.zeros(comuns.shape), where=uniao > 0)


def media_entre_pares(matriz, posicoes):
    """Média da matriz entre os pares distintos de `posicoes`."""
    sub = matriz[np.ix_(posicoes, posicoes)]
    n = len(posicoes)
    return (sub.sum() - np.trace(sub)) / (n * (n - 1))


def matriz_distancias_km(latitudes, longitudes):
    """Distância de haversine, em km, entre todos os pares de pontos."""
    lat = np.radians(np.asarray(latitudes, dtype=float))
    lon = np.radians(np.asarray(longitudes, dtype=float))
    delta_lat = lat[:, None] - lat[None, :]
    delta_lon = lon[:, None] - lon[None, :]
    termo = np.sin(delta_lat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(delta_lon / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(termo, 0, 1)))


def distancia_ao_mais_proximo(avaliacoes, posicao_do_local, distancias):
    """Distância de cada avaliação ao local mais próximo já avaliado antes pelo mesmo usuário."""
    ordenadas = avaliacoes.sort_values("data", kind="stable")
    posicoes = ordenadas["gmap_id"].map(posicao_do_local).to_numpy()
    usuarios, _ = pd.factorize(ordenadas["user_id"])
    ordem = np.argsort(usuarios, kind="stable")
    limites = np.flatnonzero(np.diff(usuarios[ordem])) + 1
    resultados = []
    for grupo in np.split(posicoes[ordem], limites):
        for i in range(1, len(grupo)):
            resultados.append(np.nanmin(distancias[grupo[i], grupo[:i]]))
    return np.array(resultados)


def ic_bootstrap(valores, grupos=None, reamostragens=2000, semente=42):
    """Média e intervalo de 95% por bootstrap, reamostrando os grupos (por padrão, cada valor)."""
    valores = np.asarray(valores, dtype=float)
    if grupos is None:
        somas, contagens = valores, np.ones(len(valores))
    else:
        codigos, _ = pd.factorize(np.asarray(grupos))
        somas = np.bincount(codigos, valores)
        contagens = np.bincount(codigos).astype(float)
    gerador = np.random.default_rng(semente)
    medias = np.empty(reamostragens)
    for i in range(reamostragens):
        sorteio = gerador.integers(len(somas), size=len(somas))
        medias[i] = somas[sorteio].sum() / contagens[sorteio].sum()
    inferior, superior = np.percentile(medias, [2.5, 97.5])
    return somas.sum() / contagens.sum(), inferior, superior


def ajustar_vieses(treino, reg=10, iteracoes=10):
    """Ajusta média global e vieses regularizados de local e de usuário."""
    media = treino["rating"].mean()
    vies_usuario = pd.Series(dtype=float)
    vies_local = pd.Series(dtype=float)
    for _ in range(iteracoes):
        residuo = treino["rating"] - media - treino["user_id"].map(vies_usuario).fillna(0)
        agrupado = residuo.groupby(treino["gmap_id"]).agg(["sum", "size"])
        vies_local = agrupado["sum"] / (agrupado["size"] + reg)
        residuo = treino["rating"] - media - treino["gmap_id"].map(vies_local)
        agrupado = residuo.groupby(treino["user_id"]).agg(["sum", "size"])
        vies_usuario = agrupado["sum"] / (agrupado["size"] + reg)
    return media, vies_usuario, vies_local


def erros_de_nota(real, previsto):
    """MAE, MSE e RMSE entre notas reais e previstas."""
    diferenca = np.asarray(real, dtype=float) - np.asarray(previsto, dtype=float)
    mse = float((diferenca**2).mean())
    return {"MAE": float(np.abs(diferenca).mean()), "MSE": mse, "RMSE": float(np.sqrt(mse))}
