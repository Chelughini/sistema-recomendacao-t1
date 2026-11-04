# Relatório — Trabalho T1 de Sistemas de Recomendação

- **Disciplina:** Sistemas de Recomendação, Escola Politécnica, PUCRS
- **Professor:** Rafael Scopel, PhD
- **Integrantes:** a definir

> Registro vivo do trabalho: descreve sempre o estado atual. Mudanças no que já foi documentado ficam em [Histórico de alterações](#histórico-de-alterações).

## Sumário

1. [Organização do projeto](#1-organização-do-projeto)
2. [Dados](#2-dados)
3. [Preparação](#3-preparação)
4. [Modelo](#4-modelo)
5. [Avaliação final](#5-avaliação-final)
6. [Interface](#6-interface)
7. [Apresentação](#7-apresentação)
8. [Entrega](#8-entrega)
9. [Histórico de alterações](#histórico-de-alterações)

## 1. Organização do projeto

A pasta do projeto contém o enunciado, o planejamento e os dois arquivos de dados brutos (`meta-Wyoming.json` e `review-Wyoming.json`), que nunca são alterados.

**Estrutura criada:**

| Pasta | Conteúdo |
|---|---|
| `src/` | Código reutilizável, importado pelos notebooks e pela interface |
| `testes/` | Testes do código de `src/` |
| `data/processed/` | Dados tratados |
| `modelos/` | Configuração e modelos gravados |
| `figuras/` | Figuras geradas pelos notebooks e telas da interface |

**Ambiente:** Windows 11 e Python 3.14.7.

| Biblioteca | Versão |
|---|---|
| pandas | 3.0.3 |
| numpy | 2.4.6 |
| scipy | 1.18.1 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.1 |
| seaborn | 0.13.2 |
| pyarrow | 24.0.0 |
| joblib | 1.6.0 |
| streamlit | 1.58.0 |
| python-pptx | 1.0.2 |
| nbformat | 5.11.1 |
| nbconvert | 7.17.2 |
| ipykernel | 7.4.0 |
| pytest | 9.2.0 |

Todas já estavam instaladas. Um notebook de teste importou as bibliotecas e foi executado com sucesso pelo nbconvert, no kernel `python3`.

**Publicação da base no Moodle:** feita.

## 2. Dados

Código em `src/dados.py`, testes em `testes/test_dados.py` e execução em `01_dados.ipynb`.

### 2.1 Leitura

A base é a Google Local Data 2021 (McAuley Lab, UCSD), estado de Wyoming, em dois arquivos com um JSON por linha, unidos pelo campo `gmap_id`.

- **Metadados:** todos os campos são lidos, sem tratamento.
- **Avaliações:** lidas linha a linha, mantendo só os locais selecionados, o que equivale a um *inner join*. Ficam `user_id`, `gmap_id`, `rating`, `time` e `text`; `pics` e `resp` viram os indicadores `tem_foto` e `tem_resposta`. O nome de quem avaliou não é carregado.

| Arquivo bruto | Medida | Valor |
|---|---|---|
| Metadados | Linhas | 12.088 |
| Metadados | `gmap_id` distintos | 12.016 |
| Metadados | Sem categoria | 88 |
| Metadados | Sem `state` (nulo ou chave ausente) | 4.623 |
| Avaliações | Linhas | 1.141.421 |
| Avaliações | De locais fora dos metadados | 0 |

Esses valores descrevem os arquivos brutos, antes do recorte e da limpeza.

### 2.2 Recorte pela categoria principal

A **categoria principal** é a primeira da lista que não seja `Caterer`. O local entra se ela for de alimentação, isto é, se casar com o padrão de palavras e não estiver na lista de exclusão. Uma categoria secundária de comida não basta: é isso que deixa de fora hotéis, postos e mercados que têm restaurante ou lanchonete.

| Etapa | Locais | Avaliações |
|---|---:|---:|
| Arquivo inteiro | 12.016 | 1.141.421 |
| Pela regra | 1.855 | 431.165 |
| Inclusão manual | 8 | 2.753 |
| **Recorte** | **1.863** | **433.918** |

As contagens são anteriores à limpeza. Dentro do recorte, nenhuma avaliação está sem `rating` ou `user_id`, 177.319 estão sem texto, 11.092 têm foto e 39.229 têm resposta do local.

**O que ficou de fora:** 151 locais com alguma categoria de comida, somando 31.412 avaliações. Os maiores grupos são hotéis (12.488 avaliações), truck stops (3.958) e mercados (1.795). O local mais avaliado desse grupo é o Little America Hotel - Wyoming, com 5.928 avaliações.

**Inclusão manual:** só entram locais cuja atividade principal é servir comida ou bebida, confirmada nos comentários, e que tenham categoria de comida ou sejam Dinner theater.

| Local | Categoria principal | Avaliações |
|---|---|---:|
| Bar J Chuckwagon Suppers | Dinner theater | 1.066 |
| The Outlaw Saloon | Concert hall | 678 |
| Yellowstone Garage | Event venue | 498 |
| The Cody Cattle Company | Dinner theater | 373 |
| Bar J Chuckwagon | Dinner theater | 52 |
| Pretzelmaker (Cheyenne) | Pretzel store | 44 |
| Sunset House Restaurant | Banquet hall | 26 |
| Pretzelmaker (Casper) | Pretzel store | 16 |

**Examinados e mantidos fora:**

- Alf's Pub, Saddle Lite Saloon, Pizza Ranch FunZone Arcade e Black Gold Grille parecem servir comida ou bebida, mas suas categorias descrevem outro negócio (loja de bebidas, salão de beleza, fliperama e espaço de eventos). Como o conteúdo vem das categorias, o vetor desses locais seria enganoso.
- Galloway's Pub & Bowling alley e Wyoming Downs OTB têm bar, mas a atividade principal é boliche e apostas.

**Limitação:** a regra também aceita alguns locais pequenos que não são restaurantes típicos, como cafeterias de escola e uma loja classificada como Food court. Eles têm poucas avaliações e continuam no recorte, para manter a regra simples.

### 2.3 Limpeza

Os arquivos brutos não são alterados. O resultado está em `data/processed/avaliacoes.parquet` (429.622 linhas, 10 colunas) e `data/processed/locais.parquet` (1.863 linhas, 19 colunas). Duas execuções seguidas geraram arquivos idênticos.

**Funil dos locais:**

| Etapa | Restam | Removidas |
|---|---:|---:|
| Linhas de metadados | 12.088 | |
| `gmap_id` repetido (cópias idênticas) | 12.016 | 72 |
| Sem categoria | 11.931 | 85 |
| Com categoria, fora do recorte | 1.863 | 10.068 |
| Sem avaliação depois da limpeza | 1.863 | 0 |

**Funil das avaliações:**

| Etapa | Restam | Removidas |
|---|---:|---:|
| Avaliações do recorte | 433.918 | |
| Sem nota ou sem usuário | 433.918 | 0 |
| Duplicatas exatas | 429.622 | 4.296 |
| Mesmo usuário e local, fica a mais recente | 429.622 | 0 |

**Decisões e verificações nas avaliações:**

| Item | Regra | Resultado |
|---|---|---|
| Notas | Inteiros de 1 a 5; outro valor interrompe a limpeza | Todas válidas |
| Datas | `time` vira `data`, `ano` e `mes` | De 27/03/2008 a 04/09/2021 |
| Texto ausente | Mantido, com o indicador `tem_texto` | 177.267 (41,3%) |
| Tradução automática | Mantida | 3.290 |
| Rajadas (5 ou mais avaliações do usuário no mesmo minuto) | Mantidas | 5.832 avaliações (1,4%) em 993 rajadas |

**Rajadas:** 209 rajadas (21,0%) têm nota constante, somando 1.199 avaliações. Entre usuários com 5 ou mais avaliações fora de rajada, a nota constante aparece em 11,7%. Mesmo assim, todas continuam: só 5 rajadas repetem texto e há menos notas 5 nelas (46,7%) que fora delas (55,8%), o que não sugere avaliações forjadas.

**Decisões e verificações nos locais:**

| Item | Regra | Resultado |
|---|---|---|
| Cidade e CEP | Extraídos do final do endereço | 115 cidades; 7 locais sem cidade e 6 sem CEP |
| Coordenadas | Fora de lat 40,5 a 45,5 e lon −111,6 a −103,5: anular | Nenhuma anulada |
| Preço | `preco_nivel` conta `$` ou `₩`, artefato da coleta | 16 com `₩`; 691 sem preço |
| Fechados | `fechado_perm` e `fechado_temp`, só pelo texto de `state`; as avaliações continuam, mas o local não é recomendado | 205 permanentes e 33 temporários |
| Colunas | Saem `url` e `hours`; `avg_rating` e `num_of_reviews` ganham o sufixo `_google` | |
| Consistência | Correlação entre `avg_rating_google` e a média na base; só conferência, pois inclui o futuro e não é *feature* | 0,991 |
| Junção | Toda avaliação tem local nos metadados e todo local tem avaliação | Confirmado |

Dos 7 locais sem cidade, 6 não têm endereço e um traz só o CEP. Todos têm coordenada.

### 2.4 Descrição da base

Base limpa, no período inteiro. Só esta descrição usa o período inteiro; as análises que orientam decisões olham apenas os dados anteriores ao corte de teste. O estilo dos gráficos está em `src/graficos.py`.

| Medida | Valor |
|---|---:|
| Avaliações | 429.622 |
| Usuários | 175.278 |
| Locais | 1.863 |
| Cidades | 115 |
| Período | 27/03/2008 a 04/09/2021 |
| Nota média | 4,15 |
| Desvio-padrão da nota | 1,21 |
| Avaliações por usuário (média) | 2,45 |
| Avaliações por local (média) | 230,6 |
| Esparsidade | 99,868% |

Quase toda combinação de usuário e local está vazia, o que limita qualquer técnica que dependa de histórico em comum.

**Notas**

![Distribuição das notas](figuras/10_distribuicao_notas.png)

A distribuição é assimétrica: 78,1% das avaliações têm nota 4 ou 5, e a nota 5 sozinha tem 55,6%. Notas de 1 a 3 são o sinal mais raro, o que apoia considerar relevante a nota 4 ou maior.

**Atividade dos usuários**

![Usuários com ao menos k avaliações](figuras/11_atividade_usuarios.png)

| Com ao menos k avaliações | Usuários | % dos usuários | % das avaliações |
|---:|---:|---:|---:|
| 1 | 175.278 | 100,0% | 100,0% |
| 2 | 59.561 | 34,0% | 73,1% |
| 3 | 34.864 | 19,9% | 61,6% |
| 5 | 18.300 | 10,4% | 48,6% |
| 10 | 7.344 | 4,2% | 32,3% |
| 20 | 2.282 | 1,3% | 16,6% |
| 50 | 176 | 0,1% | 2,7% |

Dos usuários, 66,0% têm uma única avaliação, e o mais ativo tem 136. A maioria das pessoas tem pouquíssimo histórico, o que torna importante o cenário de usuário novo.

**Popularidade**

![Cauda longa e concentração das avaliações](figuras/12_popularidade.png)

A atenção é concentrada, mas sem domínio extremo: o índice de Gini é 0,587, os 20% de locais mais avaliados têm 61,2% das avaliações e os 19 maiores (1%) têm 7,6%. A mediana é de 123 avaliações por local, contra média de 230,6. O mais avaliado é o Texas Roadhouse de Cheyenne, com 2.598.

**Nota média por usuário e por local**

![Nota média por usuário e por local](figuras/13_nota_media.png)

Entre os 18.300 usuários e os 1.811 locais com ao menos 5 avaliações, as médias são parecidas (4,20 e 4,19). Os usuários variam mais (desvio-padrão de 0,61, contra 0,47) e formam um pico perto da média 5. Os locais também variam, o que abre espaço para usar a qualidade do local como sinal.

**Categorias**

![As 20 categorias principais com mais avaliações e sua nota média](figuras/14_categorias.png)

As 20 maiores das 98 categorias principais têm 87,6% das avaliações. Fast food é a mais avaliada (74.061) e tem a menor nota entre elas (3,72), seguida de Pizza delivery (3,82); Cafe tem a maior (4,45). As categorias estão no idioma original da base.

**Cidades e mapa**

![As 15 cidades com mais avaliações](figuras/15_cidades.png)

As 15 maiores das 115 cidades têm 82,7% das avaliações, com Cheyenne (95.091), Casper (56.496) e Jackson (38.473) à frente. Evansville, vizinha de Casper, aparece com 6.383: locais muito próximos podem estar em cidades com nomes diferentes, um dos motivos para comparar cidade e distância na Fase 3.

![Mapa dos locais](figuras/16_mapa_locais.png)

Os locais formam aglomerados isolados nas cidades, com grandes áreas vazias entre eles. Isso sugere que a localização deve pesar na recomendação, hipótese medida na etapa seguinte. A cor não mostra uma região com notas sistematicamente melhores.

**Tempo**

![Avaliações e nota média por ano](figuras/17_avaliacoes_por_ano.png)

2018 e 2019 têm 57,1% das avaliações. A nota média sobe de 3,70 em 2014 para 4,24 em 2021. Dois eventos viram limitações do trabalho:

- **Pandemia:** queda de 9.357 avaliações em fevereiro de 2020 para 906 em abril, com volta a 6.640 em junho.
- **Fim da coleta:** de 7.215 em abril de 2021 para 709 em junho e só 6 em setembro.

![Avaliações por mês do ano, de 2017 a 2019](figuras/18_avaliacoes_por_mes.png)

O gráfico usa 2017 a 2019, anos completos e sem pandemia, porque no período inteiro a pandemia e o fim da coleta distorcem os meses.

| Julho em relação a fevereiro | 2017 a 2019 | Período inteiro |
|---|---:|---:|
| Todas as cidades | 2,05 | 1,45 |
| Cidades turísticas (14,2% da base) | 3,29 | 2,34 |

Essa diferença entre estações é o motivo de a validação cobrir um ano completo.

**Preço e atributos**

![Faixa de preço e atributos mais comuns](figuras/19_preco_atributos.png)

Dos locais, 37,1% não têm preço, e quase todos os demais estão nas faixas \$ e \$\$. Quase todos (99,5%) têm atributos em `MISC`, com 136 valores distintos. Entre os 15 mais comuns, 10 vêm de grupos que derivam do comportamento dos clientes (Atmosphere, Crowd, Popular for, Dining options, Offerings), viés examinado antes de definir o vetor de conteúdo.

**Texto**

![Comentários por nota](figuras/1a_texto.png)

Das avaliações, 58,7% têm comentário. Quem dá nota 1 comenta mais (77,2%, contra 48,5% na nota 3) e escreve mais (mediana de 158 caracteres, contra 53 na nota 4). O texto não entra no modelo, porque um local recém-cadastrado não teria comentários.

### 2.5 Análises para as decisões

Estas análises usam só as avaliações anteriores ao corte de teste, em 31/03/2020 (quantil 80% das datas): 343.697 avaliações, 140.895 usuários e 1.760 locais. Os metadados são uma foto de 2021. Os cálculos estão em `src/analises.py`.

| Análise | Resultado | Decisão que apoia |
|---|---|---|
| k-core | k = 5: 14.871 usuários e 48,3% das avaliações; k = 20: 875 usuários e 7,6% | Técnicas colaborativas puras atendem poucos usuários |
| Sobreposição no 5-core | 20º vizinho com 4 locais em comum (usuários) e 9 usuários em comum (locais) | Vizinhos por usuário são fracos; vizinhos por item ficam como referência |
| Notas constantes | 20,1% dos usuários com 3 ou mais avaliações; 11,1% dos com 5 ou mais | Centro 3 no perfil |
| Variância da nota | Local: 11,5%. Local + usuário, com 5 ou mais avaliações: 36,6% bruto e 29,6% ajustado | Pouco espaço para personalização |
| Estabilidade do escore | Spearman de 0,833 entre os períodos, em 1.279 locais | Usar o escore calculado no treino |
| Nota × popularidade | Spearman de −0,128 | Dois escores separados |
| Conversão × consumo | 77,6% com nota 4 ou 5; 54,2% com nota 5 | Critério duplo: conversão e AUC de gosto |
| Coerência de conteúdo | Mesmo usuário × sorteados: Jaccard de 0,0963 × 0,0851. Gostou × gostou contra não gostou × gostou: 0,0878 × 0,0964 | Categorias não indicam o gosto; o modelo precisa de mais que elas |
| Localidade | Mediana de 75,0% na cidade principal; 24,1% das avaliações em cidade nova | Componente de local, sem filtro rígido |
| Distância | Mediana de 1,3 km; 77,9% a até 10 km; P90 de 144,9 km | Testar também τ = 10 km |
| Viés dos metadados | Preço ausente em 90,3% dos locais sem avaliação e em 5,0% dos mais populares; atributos × popularidade: 0,567 | Preço fora do vetor; revisão dos atributos |
| Usuários e locais novos | 51,1% a 57,4% das avaliações de usuários novos; 1,8% a 2,7% em locais novos | Cenário 2 é o mais comum; cenário 3 é mensurável |
| Referências de nota | RMSE de 1,1951 (média global), 1,1425 (média do local) e 1,1253 (com vieses) | Referências da previsão de nota |

A diferença entre as médias de Jaccard e as reduções de MSE têm intervalo de confiança de 95% que não inclui zero. Na variância, o valor bruto de local + usuário considerando todos os usuários (64,6%) é inflado por quem tem uma única avaliação; ajustado, cai para 39,5%.

**Distância até o local já avaliado mais próximo**

![Curva acumulada da distância](figuras/1b_curva_distancia.png)

As pessoas ficam na cidade ou viajam para longe: a curva sobe até cerca de 10 km, quase para até 50 km e depois acompanha as viagens.

**Viés dos metadados**

![Atributos por local conforme a popularidade](figuras/1c_atributos_por_popularidade.png)

Retirar os grupos derivados não elimina o viés: os atributos declaráveis têm correlação até maior com a popularidade (0,596) que os derivados (0,492). Um local sem avaliações tem em média 5,5 atributos declaráveis, contra 11,0 dos mais populares. O grupo Planning inclui ainda valores que dependem do comportamento dos clientes, como Usually a wait e Quick visit. A classificação continua válida pelo critério de cadastro, e o efeito dos atributos será medido na Fase 3.

| Grupo de `MISC` | Classe | Locais | Spearman com a popularidade |
|---|---|---:|---:|
| Service options | declarável | 1.828 | 0,527 |
| Accessibility | declarável | 1.512 | 0,551 |
| Amenities | declarável | 1.435 | 0,455 |
| Payments | declarável | 770 | 0,310 |
| Planning | declarável | 459 | 0,231 |
| From the business | declarável | 81 | −0,004 |
| Popular for | derivado | 1.183 | 0,492 |
| Highlights | derivado | 1.160 | 0,218 |
| Crowd | derivado | 1.422 | 0,427 |
| Atmosphere | derivado | 1.419 | 0,266 |
| Offerings | derivado | 1.546 | 0,396 |
| Dining options | derivado | 1.246 | 0,426 |
| Health & safety | temporário | 627 | 0,376 |
| Health and safety | temporário | 13 | 0,094 |

**Conclusão sobre a técnica**

| Técnica | A favor | Contra | Cenário 2 | Cenário 3 |
|---|---|---|---|---|
| **Conteúdo e escores de produto (escolhida)** | Escore estável e local explica 11,5% da nota | Categorias não indicam gosto; atributos carregam viés de popularidade | Atende | Atende |
| Vizinhos próximos | Vizinhos por item têm suporte razoável | Por usuário, só 4 locais em comum, mesmo no 5-core | Não atende | Não atende |
| Bases de conhecimento | Não exige histórico | Não há regras de domínio prontas; usaria pouco as notas | Atende | Atende, sem personalização |
| Redes e grafos | Usa caminhos indiretos | Usuários com uma só avaliação ficam na borda do grafo | Não atende sem arestas | Não atende sem arestas |

As colunas "a favor" e "contra" vêm das análises; o que cada técnica atende nos cenários 2 e 3 é um argumento sobre o funcionamento da técnica, medido só na Fase 3. A técnica escolhida continua de pé, por ser a única que atende sozinha os três cenários usando as notas dos usuários. O limite é que o sinal de gosto vem da qualidade do local, com pouco espaço para personalização.

## 3. Preparação

Código em `src/features.py`, testes em `testes/test_features.py` e execução em `02_preparacao.ipynb`.

### 3.1 Representação de conteúdo

Só entra no vetor o que um local recém-cadastrado poderia informar e que não deriva do comportamento futuro.

| Bloco | Origem | Formato do token | Peso inicial |
|---|---|---|---|
| Categorias | Todas em `category`, normalizadas | `cat=pizza_restaurant` | 1 |
| Atributos declaráveis | `MISC`, grupos Service options, Accessibility, Amenities, Payments, Planning, From the business | `misc=service_options:delivery` | 1 |

**Fora do vetor:**

| O que fica fora | Motivo |
|---|---|
| Popular for, Highlights, Crowd, Atmosphere, Offerings, Dining options | Derivam do comportamento dos clientes; um local novo não os teria |
| Health & safety, Health and safety | Temporários da pandemia |
| Preço | Falta em 90,3% dos locais sem avaliação e em 5,0% dos mais populares, o que denuncia a popularidade; continua como filtro na interface |
| Cidade | É um componente próprio do modelo |
| Texto das avaliações | Um local novo não tem |
| `relative_results`, `avg_rating`, `num_of_reviews` | Coletados depois do corte |

**Revisão dos valores declaráveis:** dos 47 valores, 4 foram excluídos e 11 grafias foram unificadas, usando só as avaliações do treino.

| Tratamento | Valores | Motivo |
|---|---|---|
| Excluídos | `Planning: Usually a wait`, `Planning: Quick visit` | Dependem do comportamento dos clientes |
| Excluídos | `Service options: Curbside pickup` (29,0% dos abertos e 1,5% dos fechados), `Service options: No-contact delivery` (9,2% e 0,0%) | Ligados à pandemia; indicam sobretudo que o local continuava aberto na coleta |
| Unificados | 11 grafias da mesma ideia, como `Takeaway` em `Takeout` e `Toilets` em `Restroom` | Fragmentavam o vocabulário |

**Vetorização:** um TF-IDF por bloco (`sublinear_tf`, normalização L2, `min_df = 2`), ponderação por bloco, concatenação e normalização L2 final, de modo que o produto escalar seja o cosseno. Tokens desconhecidos são ignorados, o que permite vetorizar um local novo. O vetorizador é sempre ajustado só com os locais do treino correspondente, e todos os locais são transformados.

**Conferência:** ajustado com os 1.647 locais do treino, o vetor tem 167 tokens (136 de categorias e 31 de atributos) para os 1.863 locais. Todas as normas valem 1, exceto a do único local com vetor vazio (Gillette Cheese House), cuja categoria `Food` não está no vocabulário do treino.

**Limitações:**

- Os atributos declaráveis também crescem com a popularidade (Spearman de 0,596), então parte desse viés continua no vetor; o efeito é medido na Fase 3.
- Os metadados são uma foto de 2021 e também denunciam quem continuava aberto: `Takeout` aparece em 85,4% dos abertos e 27,8% dos fechados, e `Dine-in` em 72,3% e 25,9%. Esses valores continuam, por serem declaráveis e não específicos da pandemia. Como locais fechados não são recomendados, o efeito atinge sobretudo os perfis de quem os avaliou.

### 3.2 Divisão temporal

A divisão respeita o tempo: o modelo só aprende com o passado e é medido no futuro. O código está em `src/divisao.py`.

- **`corte_teste`:** quantil 80% das datas de todas as avaliações, em 31/03/2020. `treino_total` fica antes; `teste`, a partir dele.
- **`corte_validacao`:** exatamente um ano antes, em 31/03/2019, para a validação cobrir todas as estações. `treino` fica antes; `validacao`, entre os dois.
- **Hiperparâmetros:** treinar em `treino` e medir em `validacao`.
- **Modelo final:** reajustar em `treino_total` e medir uma única vez em `teste`.
- **Relevante, ou convertido:** nota 4 ou maior.

| Partição | Início | Fim | Avaliações | % da base | Usuários | Locais | % relevantes |
|---|---|---|---:|---:|---:|---:|---:|
| `treino` | 27/03/2008 | 31/03/2019 | 213.626 | 49,7% | 95.365 | 1.647 | 77,1% |
| `validacao` | 31/03/2019 | 31/03/2020 | 130.071 | 30,3% | 59.543 | 1.602 | 78,5% |
| `treino_total` | 27/03/2008 | 31/03/2020 | 343.697 | 80,0% | 140.895 | 1.760 | 77,6% |
| `teste` | 31/03/2020 | 04/09/2021 | 85.925 | 20,0% | 46.278 | 1.602 | não calculado |

O treino está acima do mínimo de 150 mil avaliações previsto. Do teste só se mostram datas e contagens; nenhuma medida ligada às notas é calculada antes da avaliação final.

**Limitações:**

- **Teste na pandemia:** 86,2% das avaliações do teste (74.081) estão no primeiro ano depois do corte, que começa com só 906 avaliações em abril de 2020. A validação é quase toda anterior à pandemia, exceto por março de 2020, que já cai para 5.075. O comportamento pode ter mudado entre as duas, então a diferença entre validação e teste não mede só a qualidade do modelo. A avaliação final compara o primeiro ano do teste com o período seguinte.
- **Coleta rarefeita no fim:** só 1.129 avaliações (1,3% do teste) são de junho de 2021 em diante, e setembro tem 6. Essa queda vem da coleta, e esse período quase não pesa nos resultados.

### 3.3 Conjuntos por cenário

| Cenário | Treino para escolher | Treino final | Alvo |
|---|---|---|---|
| 1. Usuário antigo | `treino` | `treino_total` | Segmento `antigo` |
| 2. Usuário novo | `treino` | `treino_total` | Segmento `novo` |
| 3. Local novo | `treino` sem `S_val` | `treino_total` sem `S_teste` | Antigos em locais novos |

O cenário 3 tem treino próprio, porque retirar os locais simulados de um treino único prejudicaria os cenários 1 e 2.

**Segmentos**, por avaliação do alvo, conforme o treino correspondente: `antigo` (3 ou mais avaliações), `intermediario` (1 ou 2, só para análise de sensibilidade) e `novo` (nenhuma).

| Segmento | Validação: avaliações | Usuários | % | Teste: avaliações | Usuários | % |
|---|---:|---:|---:|---:|---:|---:|
| Antigo | 33.172 | 6.779 | 25,5% | 22.089 | 6.516 | 25,7% |
| Intermediário | 18.879 | 7.234 | 14,5% | 11.016 | 5.379 | 12,8% |
| Novo | 78.020 | 45.530 | 60,0% | 52.820 | 34.383 | 61,5% |

**Locais novos:**

- **Naturais:** primeira avaliação no período-alvo. São o resultado principal do cenário 3.
- **Simulados:** `S_val` e `S_teste`, com 100 locais cada e disjuntos, sorteados com semente 42 entre locais abertos com ao menos 20 avaliações, olhando só o treino. São reportados à parte, por terem metadados mais ricos e serem mais fáceis.

| Conjunto | Origem | Locais | Abertos | Avaliações no alvo | De usuários antigos | Usuários antigos |
|---|---|---:|---:|---:|---:|---:|
| Validação | Natural | 113 | 106 | 4.603 | 1.357 | 1.047 |
| Validação | Simulado | 100 | 100 | 9.860 | 2.579 | 1.850 |
| Teste | Natural | 103 | 100 | 3.367 | 951 | 830 |
| Teste | Simulado | 100 | 100 | 6.156 | 1.567 | 1.296 |

**Treinos do cenário 3:** retirar `S_val` deixa 196.785 avaliações (16.841 a menos), e retirar `S_teste` deixa 318.092 (25.605 a menos).

**Limitação:** há poucas avaliações de usuários antigos em locais novos reais, então os intervalos de confiança do cenário 3 devem ser mais largos.

**Arquivos em `data/processed/conjuntos/`:** as 4 partições, `treino_c3`, `treino_total_c3`, `locais_novos`, `indice_locais` e `divisao.json`, com os cortes e as contagens. As partições não guardam o texto das avaliações, que não é usado no modelo. Duas execuções seguidas geraram arquivos idênticos.

### 3.4 Conferências

**Conteúdo na prática**

| Bloco | Antes do `min_df` | Depois do `min_df` |
|---|---:|---:|
| Categorias | 226 | 136 |
| Atributos | 31 | 31 |

A matriz tem 1.863 locais e 167 tokens, com 94,0% de esparsidade e mediana de 9 tokens por local. Os menores IDF são atributos muito comuns, como Delivery (1,08), e os maiores são tokens raros, como `cat=pretzel_store` (7,31).

**Vizinhos por conteúdo**

![Cinco vizinhos por cosseno de uma pizzaria, um café e um bar](figuras/20_vizinhos_conteudo.png)

Os vizinhos dos três exemplos são do mesmo tipo.

| Vetor | 5 vizinhos com a mesma categoria principal | 5 vizinhos com alguma categoria em comum |
|---|---:|---:|
| Categorias + atributos | 79,7% | 98,1% |
| Só categorias | 77,9% | 99,4% |
| Sorteados ao acaso | 5,7% | não medido |

Os atributos reduzidos não pioraram a vizinhança. O cosseno mede semelhança de tipo, não de qualidade nem de gosto: o Million Dollar Cowboy Bar fica a 0,959 de um bar de Farson porque os dois têm a categoria Bar e atributos parecidos. Os escores de produto ajudam a compensar essa limitação.

**Divisão temporal**

![Avaliações por mês com os cortes de validação e de teste](figuras/21_divisao_temporal.png)

A validação cobre um ano inteiro, incluindo o pico de verão de 2019, e termina na queda de março de 2020. O teste começa no ponto mais baixo da pandemia e se esvazia no fim da coleta.

**Verificações automáticas:** as 17 passaram. Elas conferem datas sem sobreposição, contagens que fecham, `S_val` e `S_teste` fora de seus treinos e disjuntos entre si, 100 locais em cada simulado, ao menos 20 avaliações no treino por simulado, nenhum simulado fechado, usuário novo fora do treino, antigo com 3 ou mais avaliações, local novo natural fora do treino, índice completo, divisão reproduzível e arquivos gravados iguais aos da memória. O teste é apenas gravado, sem nenhuma medida ligada às notas.

## 4. Modelo

Código em `src/metricas.py`, testes em `testes/test_metricas.py` e execução em `03_modelo.ipynb`. Tudo nesta etapa usa só treino e validação.

### 4.1 Métricas e protocolo

Todas as métricas são as vistas em aula. As definições de cobertura, novidade e serendipidade vêm da literatura geral.

| Métrica | Papel | Como é medida |
|---|---|---|
| Taxa de conversão@10 | Principal nos cenários 1 e 2 | Fração da lista que o usuário avaliou com nota 4 ou maior no período |
| Curva ROC: AUC de gosto | Principal nos cenários 1 e 2 | Entre os locais avaliados no período: nota 4 ou maior × nota 3 ou menor. Só usuários com os dois tipos; empate vale meio |
| Taxa de conversão, versão literal | Reportada | Fração da lista que o usuário avaliou, com qualquer nota |
| Curva ROC: AUC de consumo | Principal no cenário 3 | Locais convertidos × demais candidatos |
| Correlação de rankings | Confirmação | Spearman e tau-b de Kendall entre pontuação e nota, por usuário com 3 ou mais avaliações e notas variadas |
| MAE, MSE, RMSE | Só para a nota prevista | Previsão de nota contra a nota real |
| Cobertura do catálogo | Proteção contra listas repetidas | Fração dos candidatos em alguma lista |
| Cobertura dos espaços de usuários e de itens | Decisiva nos cenários 2 e 3 | Usuários com ao menos 10 locais pontuáveis; locais pontuáveis para ao menos 10 usuários |
| Novidade | Acompanhamento | Média de `−log2(fração das avaliações do local no treino)`; local sem avaliação conta como tendo uma |
| Serendipidade | Acompanhamento | Fração da lista que converte e não está na lista óbvia |
| Diversidade | Acompanhamento | Média de `1 − cosseno` entre os pares da lista |
| Intervalos de confiança | Em todas as comparações | 95%, *bootstrap* por usuário, semente 42, pareado nas diferenças; se inclui zero, é empate |

**Protocolo único**, com os mesmos usuários, candidatos e conversões para todo modelo:

- **Candidatos:** locais abertos do treino, ou uma lista informada (cenário 3).
- **Usuários:** do segmento, com ao menos uma conversão entre os candidatos; até 10.000, sorteados se passar disso.
- **Exclusão:** locais já avaliados no treino saem da lista do usuário.
- **Ordenação:** completa, sem amostrar negativos.
- **Empates:** desfeitos por sorteio com semente fixa, para não favorecer a ordem do catálogo.
- **Modelo:** uma função que devolve a matriz usuários × candidatos; `NaN` marca um par que ele não consegue pontuar.

**Conferência nos dados reais:** duas referências simples, na validação, com 6.078 usuários antigos e 1.419 candidatos. Nenhuma decisão vem delas.

| Medida | Aleatória | Popularidade |
|---|---:|---:|
| Conversão@10 | 0,0028 | 0,0204 |
| Consumo@10 | 0,0035 | 0,0229 |
| AUC de gosto | 0,4973 | 0,4858 |
| AUC de consumo | 0,5016 | 0,7394 |
| Spearman | 0,0050 | −0,0294 |
| Tau-b de Kendall | 0,0052 | −0,0272 |
| Novidade | 11,6097 | 7,8146 |
| Diversidade | 0,7616 | 0,6754 |
| Cobertura do catálogo | 100,0% | 1,3% |

A ordenação aleatória dá o que se espera do acaso: conversão@10 de 0,0028, contra 0,0029 calculados, e AUCs perto de 0,5. A popularidade converte mais (diferença de 0,0175, IC 95% de 0,0162 a 0,0188), mas empata com a aleatória na AUC de gosto (diferença de −0,0115, IC 95% de −0,0298 a 0,0071). Isso mostra por que a conversão sozinha não basta: ela mede aonde a pessoa vai, não se ela gostou.

**Limitação:** a AUC de gosto vale só para 2.397 dos 6.078 usuários, os que têm notas boas e ruins no período.

### 4.2 Componentes do modelo

Código em `src/recomendador.py` e testes em `testes/test_recomendador.py`. A conferência abaixo usa só o treino.

| Componente | Fórmula | Conferência no treino |
|---|---|---|
| Escore de qualidade | `escore_i = (v_i·R_i + m·C) / (v_i + m)`, normalizado por `(escore − 1) / 4` | `C` = 4,116; `m` = 75 (mediana das avaliações por local) |
| Escore da cidade | Mesma fórmula, com prior na média da cidade, também suavizada | Priores de 3,546 a 4,554 |
| Perfil do usuário | `p_u = Σ w_ui·x_i`, normalizado em L2, com `w_ui = nota − 3`; só notas neutras: média simples | 95.365 perfis; 5.384 só com notas neutras; 5 com vetor nulo |
| Popularidade | `pop_i = log(1 + v_i) / log(1 + máx v)`; local novo: mediana da cidade ou do catálogo | Mediana de 0,620 nos locais sem avaliação e 0,600 nos avaliados |
| Local por cidade | Fração das avaliações do usuário na cidade do candidato | Média de 0,069 |
| Local por distância | Média de `exp(−km/τ)` nos locais avaliados pelo usuário | Média de 0,072 com τ = 25 km |
| Previsão de nota | Escore + viés regularizado do usuário (`reg = 10`), limitada a [1, 5] | Viés de −1,382 a 0,793; desvio-padrão de 0,151 |

**O que a conferência mostra:**

- **A suavização funciona:** os 62 locais com média 5 têm mediana de 3 avaliações, e nenhum passa de um escore de 4,413. O maior escore entre os abertos é 4,687, do Sweet Melissa (Laramie), com média de 4,788 em 424 avaliações. Os menores são redes de fast food, como Sonic Drive-In e McDonald's, com centenas de avaliações.
- **Local novo não é penalizado:** a popularidade dos locais sem avaliação (mediana de 0,620) fica perto da dos avaliados (0,600).
- **Cidade e distância são muito parecidas:** a correlação é de 0,958 com τ = 25 km, então a comparação da Fase 3 pode terminar em empate.

**Limitação a considerar nos pesos:** os componentes têm espalhamentos muito diferentes entre os locais e usuários. O desvio-padrão é de 0,054 no escore normalizado, 0,095 na similaridade, 0,179 na popularidade e 0,220 no local por cidade. Por isso, um peso maior não significa maior importância: o escore precisa de um peso alto para mudar a ordem tanto quanto o local muda com um peso baixo. Os pesos devem ser lidos pelo efeito nas métricas.

### 4.3 Pontuação e escolha dos hiperparâmetros (cenário 1)

`s(u,i) = α·sim(u,i) + β·escore_i + γ·local_u(i) + δ·pop_i`, com `sim = (cos + 1) / 2`, pesos não negativos e soma 1.

**Critério:** entre as combinações com conversão@10 de pelo menos 95% da melhor, a de maior AUC de gosto, exigindo `α ≥ 0,1`. Em variantes, a configuração atual só muda se a melhora na AUC de gosto não for empate. As grades estão em `modelos/grades/`, e tudo é medido na validação, com 6.078 usuários antigos e 1.419 candidatos.

**Configuração congelada** (`modelos/cenario1.json`):

| Hiperparâmetro | Valor |
|---|---|
| Pesos (conteúdo / escore / local / popularidade) | 0,1 / 0,2 / 0,5 / 0,2 |
| Local | Distância com τ = 200 km |
| `m` do escore | Percentil 25 (m = 26) |
| Centro do perfil | Média do usuário; 3 para quem não varia as notas |
| Blocos do vetor | Categorias + atributos, peso 1 em cada |

| Medida na validação | Valor | IC 95% |
|---|---:|---:|
| Conversão@10 | 0,0739 | 0,0713 a 0,0766 |
| AUC de gosto (2.397 usuários) | 0,5850 | 0,5721 a 0,5981 |
| Consumo@10 | 0,0836 | |
| AUC de consumo | 0,9167 | |
| Spearman | 0,1200 | |
| Tau-b de Kendall | 0,1024 | |
| Novidade | 9,0859 | |
| Diversidade | 0,6916 | |
| Serendipidade | 0,0236 | |
| Cobertura do catálogo | 45,9% | |
| Cobertura dos usuários e dos itens | 100,0% | |

**Local e pesos foram escolhidos em conjunto.** Com pesos fixos, um τ maior achata o local e dá mais força relativa ao escore, um efeito que os pesos também produzem, e o critério continuava preferindo τ maior a cada valor testado. Por isso, a grade de 286 combinações foi rodada para cada versão de local:

| Versão | Aptas | Melhor combinação | Conversão@10 | AUC de gosto | Cobertura |
|---|---:|---|---:|---:|---:|
| Cidade | 2 | 0,1 / 0,1 / 0,6 / 0,2 | 0,0761 | 0,5168 | 51,2% |
| Distância τ = 50 km | 21 | 0,1 / 0,2 / 0,5 / 0,2 | 0,0765 | 0,5594 | 51,4% |
| Distância τ = 100 km | 20 | 0,1 / 0,2 / 0,5 / 0,2 | 0,0770 | 0,5613 | 48,3% |
| **Distância τ = 200 km** | 10 | **0,1 / 0,2 / 0,5 / 0,2** | **0,0759** | **0,5634** | **45,0%** |
| Distância τ = 400 km | 5 | 0,1 / 0,1 / 0,7 / 0,1 | 0,0770 | 0,5539 | 56,6% |
| Distância τ = 800 km | 1 | 0,1 / 0,0 / 0,8 / 0,1 | 0,0755 | 0,4727 | 57,8% |

Valores antes dos refinamentos, com limite de conversão de 0,0754. Contra a melhor combinação com cidade, a conversão empata (−0,0001, IC 95% de −0,0014 a 0,0011) e a AUC de gosto é maior (0,0466, IC 95% de 0,0381 a 0,0556). Os pesos coincidem com os de referência, mas saíram da grade.

**Refinamentos, um por vez:**

| Refinamento | Resultado | Decisão |
|---|---|---|
| `m` no percentil 25 | AUC de gosto +0,0118 (IC 95% de 0,0089 a 0,0149); conversão −0,0011 | Adotado |
| Centro pela média do usuário | AUC de gosto +0,0097 (IC 95% de 0,0049 a 0,0145); conversão −0,0009 | Adotado |
| Atributos com peso 0,5 ou só categorias | Empate nas duas métricas | Categorias + atributos ficam |
| Só atributos | Conversão −0,0017 (IC 95% de −0,0026 a −0,0008) | Descartado |
| Incluir atributos derivados | AUC de gosto +0,0042 (IC 95% de 0,0008 a 0,0076); conversão empata | Seguem fora: ganho pequeno |
| Incluir preço | Empate nas duas métricas | Segue fora |

O refino dos pesos, com 52 combinações em torno da escolhida, não os mudou.

**Fronteira entre conversão e gosto**

![Conversão e AUC de gosto por combinação de pesos](figuras/31_grade_pesos.png)

| Limiar | Pesos | Conversão@10 | AUC de gosto | Cobertura | Conversão cedida | Gosto ganho |
|---:|---|---:|---:|---:|---:|---:|
| 100% | 0,1 / 0,1 / 0,6 / 0,2 | 0,0767 | 0,5431 | 50,0% | 0,0% | 0,0000 |
| **95%** | **0,1 / 0,2 / 0,5 / 0,2** | **0,0739** | **0,5850** | **45,9%** | **3,6%** | **0,0418** |
| 90% | 0,1 / 0,3 / 0,4 / 0,2 | 0,0696 | 0,6144 | 40,7% | 9,3% | 0,0713 |
| 80% | 0,1 / 0,4 / 0,3 / 0,2 | 0,0644 | 0,6411 | 32,6% | 16,1% | 0,0980 |
| 70% | 0,1 / 0,5 / 0,3 / 0,1 | 0,0538 | 0,6677 | 35,4% | 29,8% | 0,1246 |

Conversão e gosto competem (correlação de −0,36 na grade final): cada ganho de gosto custa conversão.

**Ablação**

![Ablação dos componentes](figuras/32_ablacao.png)

| Caso | Conversão@10 | AUC de gosto | Cobertura |
|---|---:|---:|---:|
| Modelo escolhido | 0,0739 | 0,5850 | 45,9% |
| Só conteúdo | 0,0041 | 0,5321 | 99,4% |
| Só escore | 0,0031 | 0,7136 | 1,0% |
| Só local | 0,0415 | 0,4981 | 95,7% |
| Só popularidade | 0,0204 | 0,4858 | 1,3% |
| Sem conteúdo | 0,0754 | 0,5842 | 40,8% |
| Sem escore | 0,0751 | 0,4847 | 49,0% |
| Sem local | 0,0185 | 0,6300 | 6,6% |
| Sem popularidade | 0,0421 | 0,6358 | 66,5% |

- **A combinação vale mais que as partes:** nenhum componente sozinho passa de 0,0415 de conversão.
- **Local e popularidade respondem pela conversão, e o escore pelo gosto:** sem o escore, a AUC de gosto cai para 0,4847.
- **O conteúdo não melhora as métricas principais no cenário 1:** sem ele, a conversão é até maior (0,0015, IC 95% de 0,0005 a 0,0024) e a AUC de gosto empata (−0,0007, IC 95% de −0,0061 a 0,0046). A contribuição dele aqui é ampliar o catálogo, e `α` fica no mínimo exigido. O melhor com `α = 0` antes dos refinamentos (0 / 0,2 / 0,6 / 0,2) empata na conversão e tem AUC de gosto maior (0,0089, IC 95% de 0,0035 a 0,0144). O papel principal do conteúdo está no cenário 3.

**Sensibilidade:** com limiar de 90% ou 97%, os pesos mudam, como mostra a fronteira. Com usuários de 1 ou mais avaliações, uma amostra de 10.000 escolhe os mesmos pesos (conversão de 0,0598 e AUC de gosto de 0,5783).

**Limitações:**

- A escolha conjunta de local e pesos foi feita antes dos refinamentos de `m` e centro. Com a configuração final e pesos fixos, o critério apontaria τ = 400 km (conversão de 0,0716, AUC de gosto de 0,5913 e cobertura de 39,5%), comparação que tem o mesmo problema descrito acima e não foi seguida.
- "Só categorias" empata com categorias + atributos, e a escolha entre eles é frágil.
- A AUC de gosto vale só para quem tem notas boas e ruins no período.

A usuária decidiu manter o conteúdo com peso de 0,1, mesmo sem ganho nas métricas principais do cenário 1.

### 4.4 Implementação do recomendador

A classe `Recomendador`, em `src/recomendador.py`, recebe pesos, `m`, centro, tipo de local e τ, e reúne as operações:

| Operação | O que faz |
|---|---|
| `ajustar` | Ajusta com as avaliações do treino, os locais, o vetorizador e a matriz |
| `componentes`, `pontuar` | Calculam os componentes e a pontuação, em lote |
| `prever_nota` | Escore do local + viés do usuário, limitada a [1, 5] |
| `explicar` | Local bem avaliado (nota 4 ou maior) mais parecido e os 3 tokens que mais pesam |
| `recomendar` | Lista para usuário com histórico, inclusive com 1 ou 2 avaliações: abertos não avaliados, com componentes e explicação |
| `recomendar_usuario_novo` | Lista com o que a pessoa informar; tudo é opcional |
| `usuarios_para_local_novo`, `posicao_local_novo` | Usuários indicados para um local novo e a posição dele na lista de um usuário |

O dicionário em `src/traducoes.py` traduz os tokens para português (`misc=service_options:delivery` vira "Entrega"), e tokens sem tradução não aparecem. Os pesos do usuário novo e do local novo são provisórios até as etapas seguintes.

**Conferência na validação:**

- A classe dá as mesmas pontuações da etapa anterior.
- Os 167 tokens do vetor têm tradução.
- Uma lista com explicações leva 0,13 s.
- Em 100 usuários e 1.000 recomendações, nenhum local fechado ou já avaliado entrou na lista, e 99,0% das explicações têm um local parecido.

**Limitações:**

- **A lista é pouco pessoal:** um usuário de exemplo, de Cheyenne, recebe sobretudo os locais populares e bem avaliados da cidade, como Texas Roadhouse e Chick-fil-A. Isso é coerente com a ablação.
- **A explicação é uma justificativa, não a causa:** "porque você gostou de X" aponta o local mais parecido, mas o que mais pesa na posição é o local e a popularidade. Por isso, a interface deve mostrar também as barras dos componentes.

## 5. Avaliação final

*A preencher na Fase 4.*

## 6. Interface

*A preencher na Fase 5.*

## 7. Apresentação

*A preencher na Fase 6.*

## 8. Entrega

*A preencher na Fase 7.*

## Histórico de alterações

- **2026-11-03:** relatório criado na Fase 0.
- **2026-11-03:** na seção 2.1, saíram as contagens de `rating`, `user_id`, texto, fotos e respostas do arquivo inteiro, porque o notebook passou a carregar só as avaliações do recorte. Os valores do recorte estão na seção 2.2.
- **2026-11-04:** a seção 4.3 registra a escolha conjunta de local e pesos, que substituiu a escolha do local com pesos fixos prevista no plano.
