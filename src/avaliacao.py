"""Avaliação dos três cenários com a configuração congelada (Fase 4).

As mesmas funções rodam na validação, para conferir que reproduzem o notebook do modelo, e no
teste, uma única vez. Nenhuma delas escolhe nada: os pesos vêm dos modelos já ajustados.
"""

import numpy as np
import pandas as pd

from src.analises import ic_bootstrap
from src.divisao import MINIMO_USUARIO_ANTIGO, eh_relevante, simular_cadastros
from src.metricas import aplicar_cota_de_novos, auc_por_item, avaliar, comparar, montar_protocolo, posicoes_na_lista
from src.recomendador import modelo_ponderado
from src.referencias import PageRankPersonalizado, VizinhosPorItem

SEMENTE = 42
PESOS_OBVIOS = (0.0, 0.0, 0.5, 0.5)


def aleatorio(usuarios, candidatos):
    return np.random.default_rng(SEMENTE).random((len(usuarios), len(candidatos)))


def sem_conteudo(pesos, total=1.0):
    """Os pesos de escore, local e popularidade reescalados para somar `total`, sem o conteúdo."""
    resto = sum(pesos[1:])
    return (0.0,) + tuple(total * peso / resto for peso in pesos[1:])


def _vetores(modelo, candidatos):
    return modelo.matriz[modelo._posicao_local.reindex(candidatos).to_numpy()]


def cenario1(modelo, treino, alvo, locais, segmentos=("antigo",), referencias=True, completo=True):
    """Usuário antigo: o modelo, as ordenações simples e, opcionalmente, as técnicas de referência.

    Devolve o protocolo, as funções de pontuação e os resultados, nessa ordem de nomes.
    """
    protocolo = montar_protocolo(treino, alvo, locais, list(segmentos))
    componentes = modelo.componentes(protocolo.usuarios, protocolo.candidatos)
    modelos = {"modelo": modelo_ponderado(componentes, modelo.pesos), "aleatório": aleatorio}
    for nome, pesos in [
        ("popularidade", (0.0, 0.0, 0.0, 1.0)),
        ("só escore", (0.0, 1.0, 0.0, 0.0)),
        ("só local", (0.0, 0.0, 1.0, 0.0)),
        ("popularidade + local", PESOS_OBVIOS),
        ("sem conteúdo", sem_conteudo(modelo.pesos)),
    ]:
        modelos[nome] = modelo_ponderado(componentes, pesos)
    if referencias:
        vizinhos = VizinhosPorItem().ajustar(treino).pontuar(protocolo.usuarios, protocolo.candidatos, normalizar=True)
        pagerank = PageRankPersonalizado().ajustar(treino).pontuar(protocolo.usuarios, protocolo.candidatos)
        base_combinada = modelo_ponderado(componentes, sem_conteudo(modelo.pesos, 0.8))(protocolo.usuarios, protocolo.candidatos)
        modelos["vizinhos por item"] = lambda usuarios, candidatos: vizinhos
        modelos["vizinhos por item, combinado"] = lambda usuarios, candidatos: 0.2 * vizinhos + base_combinada
        modelos["PageRank personalizado"] = lambda usuarios, candidatos: pagerank
    opcoes = {}
    if completo:
        opcoes = {
            "completo": True,
            "com_correlacao": True,
            "vetores": _vetores(modelo, protocolo.candidatos),
            "modelo_obvio": modelo_ponderado(componentes, PESOS_OBVIOS),
        }
    resultados = {nome: avaliar(protocolo, funcao, **opcoes) for nome, funcao in modelos.items()}
    return protocolo, modelos, resultados


def cenario2(modelo, treino, alvo, locais, pesos_sem_informacao):
    """Usuário novo: o cadastro simulado pela primeira avaliação e os métodos da seção 3.5.

    `pesos_sem_informacao` são os do método 3 (escore + popularidade), escolhidos na validação.
    """
    cadastros, pares = simular_cadastros(alvo, locais)
    alvo_novo = alvo[alvo["user_id"].isin(cadastros.index)]
    protocolo = montar_protocolo(treino, alvo_novo, locais, ["novo"], pares_excluidos=pares)
    cadastros = cadastros.loc[protocolo.usuarios]
    candidatos = protocolo.candidatos
    componentes = {
        "nada": modelo.componentes_cadastros(cadastros[[]], candidatos),
        "cidade": modelo.componentes_cadastros(cadastros[["cidade"]], candidatos),
        "categorias": modelo.componentes_cadastros(cadastros[["cidade", "categorias"]], candidatos),
        "exemplo": modelo.componentes_cadastros(cadastros[["cidade", "local_exemplo"]], candidatos),
    }
    alfa = modelo.pesos_usuario_novo[0]
    pesos_cidade = sem_conteudo(modelo.pesos_usuario_novo)
    coincide = modelo.coincidencia_de_categorias(cadastros, candidatos)
    cidade_mais_filtro = modelo_ponderado(componentes["cidade"], pesos_cidade)(protocolo.usuarios, candidatos) + coincide
    modelos = {
        "1. popularidade": modelo_ponderado(componentes["nada"], (0.0, 0.0, 0.0, 1.0)),
        "2. escore": modelo_ponderado(componentes["nada"], (0.0, 1.0, 0.0, 0.0)),
        "3. escore + popularidade": modelo_ponderado(componentes["nada"], pesos_sem_informacao),
        "4. local + escore + popularidade": modelo_ponderado(componentes["cidade"], pesos_cidade),
        "5. modelo: + categorias com peso": modelo_ponderado(componentes["categorias"], modelo.pesos_usuario_novo),
        "5. + categorias como filtro": lambda usuarios, candidatos: cidade_mais_filtro,
        "6. + local de exemplo, mesmo peso": modelo_ponderado(componentes["exemplo"], (alfa,) + tuple(modelo.pesos_usuario_novo[1:])),
    }
    opcoes = {
        "completo": True,
        "vetores": _vetores(modelo, candidatos),
        "modelo_obvio": modelo_ponderado(componentes["cidade"], PESOS_OBVIOS),
    }
    resultados = {nome: avaliar(protocolo, funcao, **opcoes) for nome, funcao in modelos.items()}
    return protocolo, modelos, resultados


def _resumo_auc_por_local(valores):
    validos = valores[~np.isnan(valores)]
    media, inferior, superior = ic_bootstrap(validos)
    return {"locais": len(validos), "media": media, "inferior": inferior, "superior": superior}


def cenario3(modelo_c3, treino_c3, alvo, locais, novos, n=10):
    """Local novo para usuário antigo, por origem: ordenar os novos, saída A, saída B e a cota.

    `novos` é um dicionário origem -> `gmap_id` dos locais novos abertos. Usuários antigos e
    segmentos seguem o treino do cenário 3 (coluna `segmento_c3`).
    """
    alfa, gama = modelo_c3.pesos_local_novo
    contagem = modelo_c3.avaliacoes_por_usuario
    antigos = contagem.index[contagem >= MINIMO_USUARIO_ANTIGO].to_numpy().astype(str)
    convertidas = alvo[eh_relevante(alvo["rating"]) & alvo["user_id"].isin(antigos)]
    saida = {}
    for origem, ids in novos.items():
        ids = np.sort(np.asarray(ids).astype(str))
        resultado = {"avaliacoes_no_treino": int(treino_c3["gmap_id"].isin(ids).sum())}

        protocolo = montar_protocolo(treino_c3, alvo, locais, ["antigo"], coluna_segmento="segmento_c3", candidatos=ids)
        componentes = modelo_c3.componentes_local_novo(protocolo.usuarios, protocolo.candidatos)
        ordenar = {
            "aleatório": aleatorio,
            "só local": lambda usuarios, candidatos, c=componentes: c["local"],
            "só conteúdo": lambda usuarios, candidatos, c=componentes: c["conteudo"],
            "modelo": lambda usuarios, candidatos, c=componentes: alfa * c["conteudo"] + gama * c["local"],
        }
        resultado["protocolo"] = protocolo
        resultado["ordenar_modelos"] = ordenar
        resultado["ordenar"] = {nome: avaliar(protocolo, funcao, completo=True) for nome, funcao in ordenar.items()}

        componentes_a = modelo_c3.componentes_local_novo(antigos, ids)
        positivos = np.zeros((len(antigos), len(ids)), dtype=bool)
        pares = convertidas[convertidas["gmap_id"].isin(ids)]
        linha_usuario = pd.Series(np.arange(len(antigos)), index=antigos)
        coluna_local = pd.Series(np.arange(len(ids)), index=ids)
        positivos[linha_usuario[pares["user_id"]].to_numpy(), coluna_local[pares["gmap_id"]].to_numpy()] = True
        resultado["saida_a"] = {
            "modelo": auc_por_item(alfa * componentes_a["conteudo"] + gama * componentes_a["local"], positivos),
            "só local": auc_por_item(componentes_a["local"], positivos),
            "aleatório": auc_por_item(np.random.default_rng(SEMENTE).random(positivos.shape), positivos),
        }
        resultado["saida_a_resumo"] = {nome: _resumo_auc_por_local(valores) for nome, valores in resultado["saida_a"].items()}

        juntos = np.concatenate([modelo_c3.candidatos_padrao, ids])
        protocolo_b = montar_protocolo(treino_c3, alvo, locais, ["antigo"], coluna_segmento="segmento_c3", candidatos=juntos)
        eh_novo = np.isin(protocolo_b.candidatos, ids)
        pontuacoes = modelo_c3.pontuar(protocolo_b.usuarios, protocolo_b.candidatos)
        com_cota = aplicar_cota_de_novos(pontuacoes, eh_novo, protocolo_b.ja_avaliados, n=n, cota=modelo_c3.cota_novos)
        sem = avaliar(protocolo_b, lambda usuarios, candidatos: pontuacoes, k=n)
        com = avaliar(protocolo_b, lambda usuarios, candidatos: com_cota, k=n)
        posicoes = posicoes_na_lista(pontuacoes[:, ~eh_novo], protocolo_b.ja_avaliados[:, ~eh_novo], pontuacoes[:, eh_novo])
        convertidos = eh_relevante(protocolo_b.notas.toarray()[:, eh_novo])
        posicoes_convertidas = posicoes[convertidos]
        linha_b = {"usuarios": len(protocolo_b.usuarios), "com conversão em local novo": int(convertidos.any(axis=1).sum())}
        linha_b["posição mediana do convertido"] = float(np.median(posicoes_convertidas)) if len(posicoes_convertidas) else np.nan
        linha_b["convertidos no top-10 (%)"] = 100 * float((posicoes_convertidas <= n).mean()) if len(posicoes_convertidas) else np.nan
        convertidos_todos = eh_relevante(protocolo_b.notas.toarray()) & eh_novo[None, :]
        for nome, avaliado in [("sem cota", sem), ("com cota", com)]:
            listas = avaliado.listas
            validas = listas >= 0
            itens = np.where(validas, listas, 0)
            novo_na_lista = eh_novo[itens] & validas
            acerto_novo = np.take_along_axis(convertidos_todos, itens, axis=1) & validas
            linha_b[f"listas com local novo (%), {nome}"] = 100 * float(novo_na_lista.any(axis=1).mean())
            linha_b[f"listas com local novo convertido, {nome}"] = int(acerto_novo.any(axis=1).sum())
            linha_b[f"novos em alguma lista, {nome}"] = int(len(np.unique(listas[novo_na_lista])))
            linha_b[f"conversão@10, {nome}"] = float(avaliado.por_usuario["conversao"].mean())
        linha_b["novos"] = int(eh_novo.sum())
        resultado["saida_b"] = linha_b
        resultado["cota"] = comparar(com, sem, "conversao")
        saida[origem] = resultado
    return saida


def pares_roc_gosto(protocolo, pontuacoes):
    """Para a curva ROC de gosto: por usuário com notas boas e ruins, (rótulos, pontuações) dos locais avaliados."""
    pares = []
    notas = protocolo.notas
    for i in range(notas.shape[0]):
        colunas = notas.indices[notas.indptr[i] : notas.indptr[i + 1]]
        valores = notas.data[notas.indptr[i] : notas.indptr[i + 1]]
        relevantes = eh_relevante(valores)
        if relevantes.any() and (~relevantes).any():
            pares.append((relevantes, pontuacoes[i, colunas]))
    return pares


def pares_roc_consumo(protocolo, pontuacoes):
    """Para a curva ROC de consumo: por usuário, convertidos × demais candidatos ainda não avaliados."""
    convertidos = eh_relevante(protocolo.notas.toarray())
    ja_avaliados = protocolo.ja_avaliados.toarray().astype(bool)
    pares = []
    for i in range(len(protocolo.usuarios)):
        disponiveis = ~ja_avaliados[i]
        if convertidos[i, disponiveis].any() and (~convertidos[i, disponiveis]).any():
            pares.append((convertidos[i, disponiveis], pontuacoes[i, disponiveis]))
    return pares


def erros_previsao(modelo, treino, alvo, segmento="antigo"):
    """MAE, MSE e RMSE da média global, do escore e do escore + viés, com intervalos por usuário."""
    avaliacoes = alvo[(alvo["segmento"] == segmento) & alvo["gmap_id"].isin(treino["gmap_id"])]
    reais = avaliacoes["rating"].to_numpy(dtype=float)
    grupos = avaliacoes["user_id"].to_numpy()
    previsoes = {
        "média global": np.full(len(avaliacoes), modelo.parametros["C"]),
        "escore": modelo.escores["escore"].reindex(avaliacoes["gmap_id"]).to_numpy(),
        "escore + viés": modelo.prever_nota(avaliacoes["user_id"].to_numpy(), avaliacoes["gmap_id"].to_numpy()),
    }
    linhas = {}
    for nome, previsto in previsoes.items():
        absoluto, quadrado = np.abs(reais - previsto), (reais - previsto) ** 2
        mae, mae_inf, mae_sup = ic_bootstrap(absoluto, grupos=grupos)
        mse, mse_inf, mse_sup = ic_bootstrap(quadrado, grupos=grupos)
        linhas[nome] = {
            "MAE": mae, "MAE inf": mae_inf, "MAE sup": mae_sup,
            "MSE": mse, "MSE inf": mse_inf, "MSE sup": mse_sup,
            "RMSE": np.sqrt(mse), "RMSE inf": np.sqrt(mse_inf), "RMSE sup": np.sqrt(mse_sup),
        }
    return pd.DataFrame(linhas).T, {"avaliacoes": len(avaliacoes), "usuarios": int(pd.Series(grupos).nunique())}
