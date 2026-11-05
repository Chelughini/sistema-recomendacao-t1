# Planejamento — Trabalho T1 de Sistemas de Recomendação

> **Para quem executa (Claude):** este é o roteiro oficial do trabalho. Antes de começar qualquer sessão, leia este arquivo inteiro, inclusive o **Diário de execução** no fim, e o enunciado (`Trabalho T1.pdf`). Execute as fases **na ordem**, normalmente uma seção por vez, conforme a usuária pedir. Marque `[x]` ao concluir cada caixa e registre no Diário o que foi feito, os números obtidos e qualquer desvio.
>
> **Ponto de partida:** a pasta só tem os dois arquivos de dados, o enunciado e este plano. Nada está pronto: todo o código, todos os notebooks e o relatório são construídos aqui, passo a passo. Uma tentativa anterior já foi feita e apagada. O que ela ensinou está neste plano, sobretudo na Parte B.
>
> **Valores vistos na tentativa anterior** aparecem como referência para orientar e conferir. Eles usaram um recorte e uma divisão um pouco diferentes, então os números novos vão variar. **Nenhum deles vai para o relatório como resultado nem para os slides.**
>
> **Se algo aqui contradizer o enunciado, o enunciado vence**; anote o desvio.

---

## 0. Regras permanentes

Valem para todas as fases.

### Pedidos da usuária

1. **Só métricas vistas em aula** (seção A.3). Combiná-las é permitido. Recall, HitRate, nDCG, MAP e Precision **não** podem aparecer em código, tabelas, relatório ou slides, nem como complemento.
2. **Este plano pode e deve mudar.** Antes de executar cada passo, confira se o que ele supõe ainda se sustenta com os resultados mais recentes. Se não se sustentar, altere o plano, registre o motivo no Diário e avise a usuária. Mudanças de rumo, como trocar a técnica, são confirmadas com ela antes.
3. **`relatório.md` registra tudo o que é feito** e descreve sempre o estado atual. A cada passo concluído, escreva a seção correspondente, com o que foi feito, decisões, números e figuras. Se algo já documentado mudar, atualize o texto e anote em "Histórico de alterações", no fim do relatório.
4. **Figuras sempre atualizadas:** toda execução de notebook regrava `figuras/`. Confira as figuras novas e veja se o relatório continua correto.

### Validade dos resultados

5. **O teste é usado uma única vez**, na Fase 4, com todas as decisões congeladas. Antes disso, não calcule nenhuma métrica no teste nem use dados do período de teste para decidir.
6. **Decisões vêm só de treino → validação.** Análises que orientam decisões usam só dados anteriores ao corte de teste. Apenas a descrição geral da base (seção 1.4) usa o período inteiro.
7. **Toda decisão fica reproduzível em notebook.** Na tentativa anterior, comparações feitas em scripts temporários se perderam e tiveram de ser refeitas. Experimento que orienta decisão é célula de notebook, com saída gravada.
8. **Comparações com intervalo de confiança:** 95%, *bootstrap* por usuário, semente 42, pareado nas diferenças. Diferença cujo intervalo inclui zero é empate, e deve ser escrita assim.
9. **Resultado ruim é reportado como é.** Se o modelo perder para uma referência, investigue uma vez na validação; se continuar perdendo, reporte e discuta. Depois de ver o teste, não ajuste nada.
10. **Números sempre lidos das saídas**, nunca digitados de memória. Afirmações do relatório são conferidas nos dados antes de escritas.
11. **Código original:** cópia ou quase cópia de modelagens da internet zera a nota. Não adaptar notebooks públicos desta base.

### Ambiente e execução

12. Windows 11, Python 3.14, pandas 3, numpy, scipy, scikit-learn, matplotlib, seaborn, pyarrow, joblib, streamlit, python-pptx, nbformat, nbconvert, ipykernel, pytest. Na Fase 0, confira se estão instalados e instale o que faltar.
13. **Notebooks são editados diretamente, nunca gerados por script:** o grupo também pode editá-los no Jupyter, e um gerador apagaria essas edições. Antes de editar um notebook existente, leia-o. Para criar: escreva um `.ipynb` mínimo (nbformat 4.5, kernelspec `python3`), com uma célula final, e insira as demais pela ferramenta de edição de notebook, sem indicar célula, **em ordem inversa** (cada inserção vai para o início). Se o notebook com imagens for grande demais para a leitura, edite a célula com um script curto que confira o conteúdo antes de trocar.
14. **Executar notebooks** a partir da raiz, com nbconvert em modo `--execute --inplace` e um `timeout` alto. Processos longos vão para segundo plano. Depois de rodar, procure no JSON do notebook por erros e por saídas `stderr`.
15. **Terminal:** comandos longos com heredoc, aspas ou acentos falham no Git Bash deste ambiente. Script com mais de poucas linhas vai para um arquivo no scratchpad. Em Python, reconfigure a saída para UTF-8, ou o terminal quebra com `≥` e `ç`.
16. **Código reutilizável** fica em `src/`, com testes em `testes/`, e é importado pelos notebooks e pela interface. Notebooks ficam na raiz.

### Estilo

17. **Tudo em português:** markdown, variáveis, títulos de gráficos. Decimal com vírgula em textos e rótulos.
18. **Semente 42** em tudo que sorteia.
19. **Gráficos:** carregue a skill `dataviz` antes de criar os primeiros de cada sessão. Sempre um único eixo Y; duas medidas viram dois gráficos. Uma cor quando há uma única série. Salve em `figuras/` com prefixo da fase: `1x_` dados, `2x_` preparação, `3x_` modelo, `4x_` avaliação, `5x_` interface. Em rótulos, `$` precisa de escape (o matplotlib interpreta como LaTeX), e o caractere `∝` não existe na fonte.

---

## Parte A — Contexto e decisões

### A.1 Enunciado

- Construir um sistema de recomendação com **uma** técnica vista em aula, **no nível do usuário**. A base precisa conter ratings por usuário; caso contrário, a nota é zero.
- Grupo de até 5 pessoas. Base pública, de preferência diferente da dos outros grupos, **publicada no fórum do Moodle**.
- Interface simples com 3 cenários: (1) lista de itens para **usuário antigo**; (2) lista de itens para **usuário novo**; (3) **item novo** do catálogo para **usuário antigo**.
- Entregáveis: PPT; base de dados; código-fonte; apresentação em sala.

| Seção do PPT | Conteúdo | Vem de |
|---|---|---|
| a | Capa: título e integrantes | Pendência P1 |
| b | Descrição do sistema | Fase 6 |
| c | Base: estatísticas descritivas e gráficos | Seção 1.4 |
| d | Conceitos teóricos do modelo | Seção 3.9 |
| e | Tratamento de dados | Seções 1.2 e 1.3 |
| f | Critérios de treino e teste | Fase 2 |
| g | Estimação do modelo | Fase 3 |
| h | Performance com as métricas da aula | Fase 4 |
| i | Interface funcionando nos 3 cenários | Fase 5 |

### A.2 Decisões já tomadas pela usuária

| Tema | Decisão |
|---|---|
| Base | Google Local Data 2021 (McAuley Lab, UCSD), estado de Wyoming, gastronomia |
| Recorte | "Bar" entra; "Caterer" sai (restaurante que também faz catering continua) |
| Técnica | **Recomendação baseada em conteúdo e escores de produto.** Confirmada sabendo que vizinhos por item convertem cerca de 8% mais para usuários antigos, porque ela é a única que atende sozinha os 3 cenários |
| Critério dos pesos | **Entre as combinações com pelo menos 95% da melhor taxa de conversão@10, escolher a de maior AUC de gosto** |
| Taxa de conversão | Fração recomendada que foi consumida |
| Métricas | Só as da aula |
| Trabalho | Plano seguido passo a passo; o relatório acompanha tudo |

### A.3 Métricas e o papel de cada uma

Objetivo do sistema: recomendar locais aonde a pessoa iria **e** de que gostaria.

| Métrica da aula | Papel | Como medir |
|---|---|---|
| **Taxa de conversão@10** | **Principal** nos cenários 1 e 2 | Fração da lista que o usuário avaliou com nota ≥ 4 no período (`Conversao@10`). É uma aproximação offline |
| **Curva ROC: AUC de gosto** | **Principal** nos cenários 1 e 2 | Entre os locais que o usuário avaliou no período: nota ≥ 4 × nota ≤ 3. Só usuários com os dois tipos |
| Taxa de conversão, versão literal | Reportada | Fração da lista que o usuário avaliou, com qualquer nota (`Consumo@10`) |
| **Curva ROC: AUC de consumo** | **Principal** no cenário 3 | Locais convertidos × demais candidatos |
| Correlação de rankings | Confirmação | Spearman e tau-b de Kendall entre pontuação e nota, por usuário com ≥ 3 avaliações e notas variadas. É lenta, então só para finalistas |
| MAE, MSE, RMSE | Só para a nota prevista; não escolhem pesos | Previsão: escore do local + viés do usuário |
| Cobertura do catálogo | Proteção contra listas repetidas | Fração dos candidatos em alguma lista |
| Cobertura dos espaços de usuários e de itens | Decisiva nos cenários 2 e 3 | Usuários com ≥ 10 locais pontuáveis; locais pontuáveis para ≥ 10 usuários, separando os novos |
| Novidade | Acompanhamento | Média de `−log2(fração das avaliações do local no treino)` |
| Serendipidade | Acompanhamento | Fração da lista que converte e não está na lista óbvia (popularidade + local) |
| Diversidade | Acompanhamento | Média de `1 − cosseno` entre os pares da lista |
| Intervalos de confiança | Em todas as comparações | Regra 8 |

**Por que esses papéis:**

- **Conversão sozinha não basta.** Cerca de 78% do que é consumido tem nota ≥ 4, então ela mede sobretudo *aonde a pessoa vai*. Na tentativa anterior, conversão e AUC de gosto tiveram correlação negativa (−0,29) entre as combinações de pesos.
- **AUC de consumo** quase não separa os modelos combinados no cenário 1 (todos perto de 0,90), mas serve no cenário 3, em que a pergunta é se o local novo fica acima dos outros.
- **MAE, MSE e RMSE** medem só locais já avaliados, e o modelo ordena locais em vez de prever nota. MSE é o RMSE ao quadrado; é reportado por constar da lista da aula.
- **Correlação de rankings** conclui o mesmo que a AUC de gosto, mas sofre com notas empatadas e poucas avaliações por usuário.
- **Novidade, serendipidade e diversidade** não têm um valor ótimo claro: a popularidade pura tem diversidade alta e a lista aleatória tem novidade máxima.

As definições de cobertura, novidade e serendipidade vêm da literatura geral. Confira com os slides da disciplina (Pendência P2).

### A.4 Dados

| Arquivo | Linhas | Campos |
|---|---|---|
| `review-Wyoming.json` | 1.141.421 | `user_id`, `name`, `time` (ms), `rating` (1–5), `text`, `pics`, `resp`, `gmap_id` |
| `meta-Wyoming.json` | 12.088 | `gmap_id`, `name`, `address`, `latitude`, `longitude`, `category` (lista), `avg_rating`, `num_of_reviews`, `price`, `hours`, `MISC` (grupo → lista de valores), `state`, `relative_results`, `description`, `url` |

Um JSON por linha. As avaliações têm `user_id → gmap_id → rating`, mas não dizem o tipo do local; é a `category` dos metadados que seleciona a gastronomia. Os arquivos se unem pelo campo `gmap_id`. **Os brutos nunca são alterados.**

**Armadilhas técnicas já encontradas:**

- O pandas 3 transforma `None` em `NaN` nas colunas de texto. Verificações de cidade ou categoria devem testar se o valor é texto, não se é `None`.
- O Parquet devolve listas como `ndarray` e preenche os grupos ausentes de `MISC` com `None`.
- O vetorizador precisa de uma função nomeada no lugar de `lambda`, ou o joblib não consegue salvá-lo.
- Peso 0 em um bloco deixa zeros explícitos na matriz esparsa, que precisam ser eliminados.
- A leitura de avaliações deve ser linha a linha (o arquivo tem ~350 MB).

---

## Parte B — O que já sabemos

### B.1 Sobre os dados

| Achado | Evidência | Consequência |
|---|---|---|
| Matriz muito esparsa | Esparsidade de ~99,9%; metade dos usuários com uma única avaliação | Técnica colaborativa pura atende poucos usuários |
| Notas com viés positivo | Cerca de 78% são 4 ou 5 | Relevante = nota ≥ 4; conversão quase igual a consumo |
| Usuários muito locais | Mediana de ~79% das avaliações na cidade principal; 22% das avaliações em cidade nunca visitada | Localização é o sinal mais forte para conversão |
| Muitos usuários novos no futuro | ~60% das avaliações depois do corte; ~4% de locais novos | Cenário 2 é o caso mais comum |
| Vizinhos por usuário são fracos | 20º vizinho tem ~4 locais em comum; no de local, ~10 usuários | Vizinhos por item seriam a alternativa colaborativa |
| Notas constantes | ~12% dos usuários com ≥ 5 avaliações dão sempre a mesma nota | Centro 3 no perfil; centrar pela média apagaria esses perfis |
| Categoria sozinha não indica gosto | Jaccard "não gostou×gostou" 0,091 ≥ "gostou×gostou" 0,081 | Conteúdo precisa de mais que categoria |
| Pouca variância explicada | Local explica ~11% da nota; local + usuário, ~35% entre usuários com ≥ 5 avaliações | Espaço pequeno para personalização |
| Escore é estável | Spearman de ~0,79 da média do local entre períodos | O escore do treino prevê o futuro |
| Popular não é sinônimo de bom | Spearman de ~−0,16 entre nota e popularidade | Escore e popularidade são componentes separados |
| Forte sazonalidade | Julho tem o dobro de avaliações de fevereiro; 3,7 vezes em cidades turísticas | Validação precisa de um ano completo |
| Pandemia e fim da coleta | Queda de ~9,9 mil avaliações (02/2020) para ~1 mil (04/2020); poucos dados a partir de 06/2021 | Limitações a declarar; medir o teste em dois períodos |
| Metadados são uma foto de 2021 | Nº de atributos tem correlação de 0,56 com a popularidade | Cuidado com vazamento (abaixo) |

### B.2 Sobre o modelo (resultados orientativos, cenário 1, validação)

Pesos na ordem conteúdo / escore / local / popularidade.

| Ordenação | Conversão@10 | AUC de gosto | Cobertura do catálogo |
|---|---|---|---|
| Aleatória | 0,0020 | 0,51 | 100% |
| Só escore | 0,0038 | 0,70 | 1% |
| Só conteúdo | 0,0063 | 0,49 | 93% |
| Popularidade | 0,0143 | 0,49 | 1% |
| Só cidade | 0,0241 | 0,50 | 91% |
| Popularidade + cidade | 0,0567 | 0,49 | 43% |
| Sem popularidade, melhor conversão | ~0,045 | ~0,57 | ~88% |
| Melhor conversão: 0,2 / 0,1 / 0,5 / 0,2 | 0,0618 | 0,52 | 59% |
| **Pelo critério adotado: 0,1 / 0,2 / 0,5 / 0,2** | **0,0605** | **0,57** | **49%** |
| Vizinhos por item, combinado | 0,0666 | 0,51 | 56% |

O que isso ensina:

- **A combinação vale muito mais que cada parte.** Por isso os escores de produto incluem a **popularidade**, além da média bayesiana: a fórmula só com qualidade perdia ~36% de conversão.
- **O sinal de gosto vem da qualidade do local, não da afinidade pessoal.** É uma limitação a declarar.
- **O conteúdo acrescenta pouco à conversão, mas amplia o catálogo**, e é o único jeito de recomendar um local novo. Peso alto de conteúdo piora a conversão.
- **Vizinhos por item não pontuam nenhum local novo** (0% contra 100% do conteúdo), o que justifica a técnica.
- **Previsão de nota:** escore + viés do usuário (RMSE ~0,98) supera escore (~1,04) e média global (~1,09); somar conteúdo não melhora.
- **Cenário 2:** cidade + escore + popularidade supera muito os rankings globais. Só o escore é fraco. Categorias declaradas com peso 0,2 pioraram; um local de exemplo com peso 0,2 ajudou um pouco e ampliou a cobertura.
- **Cenário 3:** conteúdo somado à cidade melhora os locais novos (conversão@10 de 0,0566 para 0,0686; AUC de consumo de 0,84 para 0,87), com peso baixo de conteúdo (0,1).

### B.3 Erros que este plano evita

| # | Erro cometido na tentativa anterior | Evidência | Como evitar |
|---|---|---|---|
| 1 | **Locais que não são restaurantes** entravam por uma categoria secundária de comida | 159 locais e 7% das avaliações: hotéis (o Little America Hotel era o local mais avaliado), postos, mercados, livrarias | Recorte pela **categoria principal** (seção 1.2) |
| 2 | **Atributos derivados do comportamento** usados como conteúdo (Popular for, Highlights, Crowd, Atmosphere, Offerings, Dining options). São de 2021 e um local recém-cadastrado não os teria | Retirá-los empatou no cenário 1 e custou pouco no 3 (0,0674 × 0,0686) | Só atributos declaráveis |
| 3 | **Preço denunciava a popularidade** | `desconhecido` em 91% dos locais novos reais contra 38% dos demais; retirá-lo empatou | Fora do vetor; só filtro na interface |
| 4 | **Retirar locais simulados de um treino único** prejudicava os cenários 1 e 2 | 31.625 avaliações e 301 usuários antigos a menos | Treino próprio para o cenário 3 |
| 5 | **Locais simulados escolhidos com dados do teste** e iguais em validação e teste | Viés de seleção | Conjuntos disjuntos, escolhidos só com o treino |
| 6 | **Locais simulados tratados como iguais aos novos reais**, embora tenham metadados mais ricos | 20,2 × 14,2 atributos em média | Resultado principal com os locais novos reais |
| 7 | **Validação só de agosto a março**, sem o verão | Sazonalidade | Um ano completo |
| 8 | **Cidade como texto** ignora cidades vizinhas e 38 locais sem cidade | Distância com τ = 50 km: 0,0618 × 0,0605 (intervalo de +0,0002 a +0,0024), sem refinar os pesos | Comparar distância e cidade |
| 9 | **Métricas fora da aula** e **experimentos em scripts temporários** | Comparações tiveram de ser refeitas | Regras 1 e 7; métricas antes do modelo |
| 10 | **Média simples da cidade como prior** | Cidade pequena virava prior 5,0 | Suavizar também a média da cidade |

**Testado e descartado:** decaimento temporal no perfil (sem ganho); marca do estabelecimento como informação de conteúdo (empate); kNN de conteúdo e Naive Bayes (não superam o perfil TF-IDF); previsão de nota por kNN de conteúdo (pior que a média global); `relative_results` no cenário 3 (coletado depois do corte, possível vazamento); texto das avaliações no vetor (local novo não tem).

---

## Parte C — Estrutura de pastas ao final

```
Sistema de Recomendações/
├── PLANEJAMENTO.md
├── relatório.md                  registro vivo do trabalho
├── README.md, requirements.txt   Fase 7
├── Trabalho T1.pdf
├── meta-Wyoming.json, review-Wyoming.json   brutos, nunca alterar
├── 01_dados.ipynb                Fase 1
├── 02_preparacao.ipynb           Fase 2
├── 03_modelo.ipynb               Fase 3 (só validação)
├── 04_avaliacao.ipynb            Fase 4 (teste, uma vez)
├── app.py                        Fase 5
├── src/      dados.py, graficos.py, analises.py, features.py, divisao.py, metricas.py, recomendador.py, referencias.py, avaliacao.py, interface.py
├── testes/   test_*.py
├── data/processed/, modelos/, figuras/
├── apresentacao/T1_Sistema_Recomendacao.pptx
└── scripts/  capturar_telas.py (Fase 5), gerar_ppt.py (Fase 6)
```

---

## Pendências com a usuária (perguntar quando a fase chegar)

- [ ] **P1 — Integrantes e título** (Fase 6). Título provisório aprovado em 2026-11-05: "Onde comer em Wyoming: recomendação por conteúdo e escores de produto"; faltam os integrantes.
- [x] **P2 — Definições** de cobertura, novidade e serendipidade: a usuária decidiu em 2026-11-03 usar as da seção A.3. Declarar nos slides que vêm da literatura geral.
- [x] **P3 — Template do PPT** (Fase 6): o modelo simples da usuária no Canva (`modelo_ppt_canva_01.pdf`); o `.pptx` gerado é a base para ela montar os slides finais no Canva.
- [ ] **P4 — Entrega da base:** os brutos têm ~365 MB (Fase 7). Padrão: dados processados, link da fonte e notebooks que regeneram tudo.
- [x] **P5 — A base já foi publicada no Moodle?** (Fase 0). Sim, confirmado pela usuária em 2026-11-03.
- [ ] **P6 — Data da apresentação** (opcional, para o roteiro de fala).

---

## Fase 0 — Organização

- [x] Conferir que a pasta tem os dois arquivos de dados, o enunciado e este plano. Se houver outros arquivos, perguntar antes de mexer.
- [x] Conferir as bibliotecas (regra 12) e instalar o que faltar.
- [x] Criar `src/`, `testes/`, `data/processed/`, `modelos/`, `figuras/` e `src/__init__.py`.
- [x] Criar `relatório.md` com título, disciplina (Sistemas de Recomendação, Escola Politécnica, PUCRS), professor (Rafael Scopel, PhD), integrantes "a definir", sumário e "Histórico de alterações".
- [x] Resolver P5.

**Pronto quando:** a estrutura existe e o ambiente roda.

---

## Fase 1 — Dados: `src/dados.py`, `testes/test_dados.py`, `01_dados.ipynb`

**Objetivo:** recortar, limpar e entender a base, com a descrição para o slide c e as análises que justificam as decisões.

### 1.1 Leitura

- [x] Ler os metadados e, linha a linha, as avaliações, mantendo só os `gmap_id` selecionados, o que equivale a um *inner join*. Guardar `user_id`, `gmap_id`, `rating`, `time`, `text`; `pics` e `resp` viram indicadores `tem_foto` e `tem_resposta`.

### 1.2 Recorte pela categoria principal

- [x] A **categoria principal** é a primeira da lista que não seja `Caterer`, para que um restaurante cuja lista começa em `Caterer` continue, como decidido.
- [x] O local entra se a categoria principal for de alimentação. **Padrão de palavras:** restaurant, café/cafe, cafeteria, coffee, espresso, pizz, bakery, diner, grill, steak, burger, sandwich, deli, bistro, brew, ice cream, donut/doughnut, taco, burrito, sushi, buffet, bbq, barbecue, breakfast, brunch, dessert, bagel, bar, pub, gastropub, tavern, lounge, eatery, snack, juice, tea house, bubble tea, frozen yogurt, creamery, winery, cupcake, chocolate shop/cafe, wings, chicken, noodle, ramen, pho, crepe, smokehouse, chophouse, food court, hoagie, cheesesteak, bun shop, food, food and drink. Palavras curtas como `bar`, `pub`, `deli` e `pho` precisam de limite de palavra, ou `Barber shop` entraria.
- [x] **Excluir** categorias que têm essas palavras mas não são locais de consumo: Caterer, Catering food and drink supplier, Health food store, Organic food store, Food store, Wholesale food store, Food bank, Food producer, Food products supplier, Food service, Restaurant supply store, Bar stool supplier, Grill store, BBQ area, Coffee machine supplier, Coffee vending machine, Coffee wholesaler, Wholesale bakery, Chocolate factory, Tea store, Internet cafe, Bed & breakfast, Travel lounge, Hookah bar.
- [x] **Incluir manualmente** locais de comida com categoria principal atípica, listados por `gmap_id`: Bar J Chuckwagon Suppers, Bar J Chuckwagon, The Cody Cattle Company, The Outlaw Saloon, Yellowstone Garage, Sunset House Restaurant e duas unidades da Pretzelmaker. Critério: a atividade principal é servir comida ou bebida, confirmada nos comentários, e o local tem categoria de comida ou é Dinner theater.
- [x] Mostrar no notebook as categorias aceitas e rejeitadas e, entre os locais com alguma categoria de comida que ficaram fora, os maiores grupos e os 12 locais com mais avaliações. **Inspecionar:** se aparecer outro restaurante legítimo de fora, ajustar a inclusão manual e registrar.
- [x] **Referência:** ~1.857 locais e ~429 mil avaliações. Devem sair: hotéis, truck stops, mercados, general stores, livrarias, boliche, postos.

### 1.3 Limpeza

| Passo | Regra | Referência |
|---|---|---|
| `gmap_id` repetido nos metadados | Conferir que são cópias idênticas; manter uma | 72 no arquivo inteiro |
| Sem categoria | Ficam fora | 88 no arquivo inteiro |
| `rating` nulo | Remover; conferir que também não têm `user_id` | ~1,3 mil |
| Duplicatas exatas | Mesmos usuário, local, horário, nota e texto: remover | ~4,5 mil |
| Mesmo usuário e local mais de uma vez | Manter a avaliação mais recente | Nenhum caso depois das duplicatas |
| Faixa das notas | Verificar: inteiros de 1 a 5 | |
| `text` nulo | Manter; indicador `tem_texto` | ~40% |
| Rajadas (≥ 5 avaliações do usuário no mesmo minuto) | Inspecionar; manter se as notas variam | ~1,4%; 21% com nota constante |
| Tradução automática | Contar textos com "(Translated by Google)"; manter | ~3,7 mil |
| Datas | `time` em ms vira `data`, `ano`, `mes` | |
| Cidade e CEP | Extrair do final do endereço (`..., Cidade, WY 82520`) | ~38 sem cidade |
| Coordenadas | Fora de lat 40,5–45,5 e lon −111,6 a −103,5: anular | 1 (Grasslands Market, lat 28,6) |
| Preço | Contar `$` ou `₩` (artefato da coleta) em `preco_nivel` | 16 com `₩` |
| Fechados | `fechado_perm` e `fechado_temp` a partir de `state`. **Manter** como indicador: as avaliações mostram gosto, mas o local não é recomendado | ~211 e ~33 |
| Colunas sem uso | Remover `url` e `hours`; renomear `avg_rating` e `num_of_reviews` para `..._google` | |
| Consistência | Correlação entre `avg_rating` e média na base. Só conferência: inclui o futuro, então **não é feature** | ~0,99 |
| Junção | Todo `gmap_id` de avaliações existe nos metadados; remover locais sem avaliação | |

- [x] Tabela com o funil de avaliações e os removidos em cada etapa (slide e).
- [x] Gravar `data/processed/avaliacoes.parquet` e `locais.parquet`. Conferir que rodar de novo gera o mesmo resultado.
- [x] **Testes à mão:** `[Caterer, Restaurant]` entra; `[Hotel, Restaurant]` sai; `[Restaurant, Hotel]` entra; `Barber shop` sai; valor ausente não quebra; extração de cidade; preço com `₩`; coordenada fora de Wyoming; duplicata exata e avaliação repetida.

### 1.4 Descrição da base (período inteiro; slide c)

Figuras `1x_`, cada uma com a interpretação ao lado.

- [x] Visão geral: avaliações, usuários, locais, cidades, período, nota média e desvio, esparsidade.
- [x] Distribuição das notas.
- [x] Atividade dos usuários: tabela de usuários com ≥ k avaliações (k = 1, 2, 3, 5, 10, 20, 50) e gráfico.
- [x] Popularidade: cauda longa, concentração e índice de Gini.
- [x] Nota média por usuário e por local.
- [x] Top 20 categorias, com nota média.
- [x] Top 15 cidades e mapa dos locais (tamanho por avaliações, cor por nota).
- [x] Avaliações por ano e nota média por ano, em dois gráficos empilhados.
- [x] Avaliações por mês do ano, geral e em cidades turísticas (Jackson, Cody, Moran, Alta, Wapiti, Dubois, Pinedale), em gráficos separados. O gráfico usa 2017 a 2019; as razões do período inteiro ficam no texto.
- [x] Faixa de preço e atributos de `MISC` mais comuns.
- [x] Texto: fração com comentário e tamanho por nota (breve; o texto não é usado no modelo).

### 1.5 Análises para as decisões (só antes do corte de teste)

Calcule o corte de teste (quantil 80% das datas) e filtre antes destas células. **Cada análise termina com uma frase dizendo qual decisão ela apoia.**

- [x] **k-core** (k = 1, 3, 5, 10, 20): usuários, locais, avaliações e densidade. Apoia: limites da técnica colaborativa.
- [x] **Sobreposição no 5-core:** vizinhos com ≥ m co-avaliações (m = 2, 3, 5, 10) e suporte do 20º vizinho, para usuários (amostra de 1.000, por memória) e locais. Apoia: por que não vizinhos por usuário.
- [x] **Notas constantes:** % de usuários com nota sempre igual, por ≥ k avaliações. Apoia: centro 3 no perfil.
- [x] **Decomposição da variância da nota** em local e usuário. Apoia: quanto sinal pessoal existe.
- [x] **Estabilidade do escore:** Spearman da média do local entre dois períodos. Apoia: usar o escore do treino.
- [x] **Nota × popularidade.** Apoia: dois escores separados.
- [x] **Conversão × consumo:** % das avaliações com nota ≥ 4 e com nota 5. Apoia: critério duplo.
- [x] **Coerência de conteúdo:** Jaccard de categorias entre locais do mesmo usuário × sorteados com a mesma popularidade; "gostou×gostou" × "não gostou×gostou". Apoia: conteúdo além da categoria.
- [x] **Localidade:** % na cidade principal, nº de cidades por usuário, % de avaliações em cidade nunca visitada e nota nelas. Apoia: componente de local.
- [x] **Curva de distância:** para cada avaliação de usuário com histórico, a distância até o local já avaliado mais próximo; histograma e percentis. Apoia: valores de τ.
- [x] **Viés dos metadados:** nº de atributos por faixa de popularidade; `MISC` e preço ausentes nos locais com poucas avaliações × demais; tabela dos grupos de `MISC` com a classificação declarável × derivado. Apoia: seção 2.1.
- [x] **Usuários e locais novos ao longo do tempo:** em cortes de 70% e 80% dentro do período antes do corte de teste, % de avaliações de usuários e de locais novos. Apoia: peso dos cenários 2 e 3.
- [x] **Referências ingênuas de nota:** MAE, MSE e RMSE de média global, média do local e vieses, em divisão temporal.
- [x] **Conclusão:** tabela técnica × evidência, para as 4 técnicas do enunciado. Conferir se a técnica escolhida continua de pé (regra 2).

**Avisar a usuária** do efeito do recorte, com os números.

**Pronto quando:** notebook roda inteiro sem erro, testes passam, relatório cobre base, recorte, limpeza e análises.

---

## Fase 2 — Preparação: `src/features.py`, `src/divisao.py`, `testes/`, `02_preparacao.ipynb`

**Objetivo:** transformar cada local em vetor e separar os dados, sem vazamento.

### 2.1 Representação de conteúdo

Só informação que um local recém-cadastrado teria e que **não** deriva do comportamento futuro.

| Bloco | Origem | Formato do token | Peso inicial |
|---|---|---|---|
| Categorias | Todas em `category`, normalizadas (minúsculas, espaços viram `_`) | `cat=pizza_restaurant` | 1 |
| Atributos declaráveis | `MISC`, grupos Service options, Accessibility, Amenities, Payments, Planning, From the business | `misc=service_options:delivery` | 1 |

- [x] **Fora do vetor, com o motivo documentado:** Popular for, Highlights, Crowd, Atmosphere, Offerings, Dining options (derivados do comportamento); Health & safety e Health and safety (temporários da pandemia); preço (a ausência denuncia a popularidade; continua como filtro); cidade (componente próprio); texto das avaliações (local novo não tem); `relative_results`, `avg_rating` e `num_of_reviews` (coletados depois do corte).
- [x] **Rever os valores dos grupos declaráveis (achado da seção 1.5):** excluir os que dependem do comportamento dos clientes (`Planning: Usually a wait`, `Planning: Quick visit`); avaliar os que surgiram na pandemia em Service options (como `No-contact delivery` e `Curbside pickup`); unificar grafias da mesma ideia (`Takeout` e `Takeaway`, `Bar onsite` e `Bar on site`, `Wheelchair accessible` e `Wheelchair-accessible`). Os atributos declaráveis também crescem com a popularidade (Spearman de 0,596), então esse viés continua e é medido na Etapa 3 da Fase 3.
- [x] Função que gera os tokens de um local, aceitando uma linha da tabela ou um cadastro manual (categorias e atributos).
- [x] Vetorizador com um TF-IDF por bloco (`sublinear_tf`, normalização L2, `min_df = 2`), ponderação por bloco, concatenação e normalização L2 final, de modo que o produto escalar seja o cosseno. Tokens desconhecidos são ignorados, o que permite vetorizar um local novo. Método para os nomes das features, usado nas explicações. Pesos dos blocos configuráveis.
- [x] **Sempre ajustar só com os locais do treino correspondente.** Todos os locais são transformados, inclusive os novos.
- [x] **Testes à mão:** normas iguais a 1; local novo com categoria inexistente; peso 0 remove o bloco; salvar e carregar reproduz o resultado; grupos excluídos nunca geram token.

### 2.2 Divisão temporal

- [x] `corte_teste` = quantil 80% das datas de todas as avaliações (referência: março de 2020). `treino_total` = antes; `teste` = a partir dele.
- [x] `corte_validacao` = `corte_teste` menos **exatamente um ano**, para a validação cobrir todas as estações. `treino` = antes; `validacao` = entre os dois.
- [x] Hiperparâmetros: treinar em `treino`, medir em `validacao`. Modelo final: reajustar em `treino_total` e medir uma vez em `teste`.
- [x] **Conferir** que o `treino` tem pelo menos ~150 mil avaliações. Se não, reavaliar e registrar (regra 2).
- [x] Relevante/convertido: nota ≥ 4.
- [x] **Registrar as limitações:** teste na pandemia; coleta rarefeita no fim.

### 2.3 Conjuntos por cenário

| Cenário | Treino para escolher | Treino final | Alvo |
|---|---|---|---|
| 1. Usuário antigo | `treino` | `treino_total` | Segmento `antigo` |
| 2. Usuário novo | `treino` | `treino_total` | Segmento `novo` |
| 3. Local novo | `treino` sem `S_val` | `treino_total` sem `S_teste` | Antigos em locais novos |

- [x] **Segmentos**, por avaliação do alvo, conforme o treino correspondente: `antigo` (≥ 3 avaliações), `intermediario` (1 ou 2, só análise de sensibilidade), `novo` (nenhuma). Guardar também o nº de avaliações no treino.
- [x] **Locais novos naturais:** primeira avaliação no período-alvo. **São o resultado principal do cenário 3.**
- [x] **Locais novos simulados:** `S_val` e `S_teste`, 100 locais cada, **disjuntos**, sorteados entre locais abertos com ≥ 20 avaliações, **usando só o treino**: `S_val` a partir de `treino`; `S_teste` a partir de `treino_total`, sem os de `S_val`. Nenhum critério olha o período-alvo. Servem para ter mais casos, e são reportados à parte, avisando que são mais fáceis.
- [x] Gravar as partições, os treinos do cenário 3, a lista de locais novos (origem e conjunto), os cortes e contagens, e o índice `gmap_id` → linha da matriz. Vetorizadores e matrizes são gerados depois, pois dependem de cada treino.

### 2.4 Notebook

- [x] Objetivo e decisões, ligados às análises da Fase 1.
- [x] Tokens de uma pizzaria, um café e um bar; vocabulário por bloco, antes e depois do `min_df`.
- [x] Matriz: dimensão, esparsidade, tokens com menor e maior IDF, conferência das normas e de vetores vazios.
- [x] **Sanidade:** os 5 vizinhos por cosseno de uma pizzaria, um café e um bar devem ser do mesmo tipo (figura `20_vizinhos_conteudo`). Se piorarem com os atributos reduzidos, investigar antes de seguir.
- [x] Partições com datas, usuários, locais e % de relevantes (exceto no teste, que só mostra datas e contagens até a Fase 4); linha do tempo mensal com os cortes (figura `21_divisao_temporal`); segmentos; locais novos.
- [x] **Verificações automáticas:** datas sem sobreposição; contagens fecham; `S_val` fora do treino dele; `S_teste` fora do treino dele; conjuntos disjuntos; usuário novo fora do treino; antigo com ≥ 3; local novo natural fora do treino; todo local com linha na matriz; nenhum simulado fechado; divisão reproduzível. **O teste só é gravado, sem nenhuma métrica.**
- [x] **Testes à mão** da divisão, com uma base pequena.

**Pronto quando:** tudo acima passa e o relatório descreve os critérios de treino e teste (slide f).

---

## Fase 3 — Modelo: `src/metricas.py`, `src/recomendador.py`, `src/referencias.py`, `testes/`, `03_modelo.ipynb`

**Tudo na validação.** A ordem importa: **métricas primeiro**, porque cada decisão seguinte depende de medir.

### 3.1 Métricas e protocolo

- [x] Resolver P2.
- [x] Implementar as métricas da seção A.3: conversão, AUC e curva ROC, MAE, MSE, RMSE, correlação de rankings, coberturas, novidade, serendipidade, diversidade, intervalo de confiança.
- [x] **Protocolo único de avaliação**, com os mesmos usuários, candidatos e conversões para todo modelo:
  - candidatos: locais abertos do treino, ou uma lista informada (cenário 3);
  - usuários: do segmento, com ≥ 1 conversão entre os candidatos; até 10.000, sorteados se passar disso;
  - locais já avaliados no treino saem da lista do usuário;
  - ordenação completa, sem amostrar negativos;
  - empates desfeitos por sorteio com semente fixa, para não favorecer a ordem do catálogo;
  - o modelo entra como uma função que devolve a matriz usuários × candidatos;
  - disponibiliza os valores por usuário, para os intervalos de confiança.
- [x] **Testes à mão:** cada métrica com resultado conhecido; AUC com empate vale meio; correlação sem variação não quebra; protocolo numa base pequena (exclui fechados, locais fora do treino, já avaliados e outros segmentos).

### 3.2 Componentes do modelo

- [x] **Escore de qualidade (média bayesiana):** `escore_i = (v_i·R_i + m·C) / (v_i + m)`. `C` = média do treino; `m` = percentil de `v_i`; sem avaliações, `escore = C`. Normalizado: `(escore − 1) / 4`. Também o `escore_cidade`, com prior na média da cidade **suavizada pela mesma fórmula**, e a posição do local na cidade, só entre abertos.
- [x] **Perfil do usuário:** `p_u = Σ w_ui·x_i`, normalizado L2, com `w_ui = nota − centro`. Centro padrão: 3. Só notas neutras: média simples dos vetores. Na opção de centro pela média do usuário, quem não varia as notas usa 3. Pesos que se cancelam geram vetor nulo, que fica com similaridade neutra.
- [x] **Popularidade:** `pop_i = log(1 + v_i) / log(1 + máx v)`. Local novo: mediana dos locais avaliados da mesma cidade, ou do catálogo, para não ser penalizado só por ser novo.
- [x] **Local**, em duas versões a comparar:
  - `cidade`: fração das avaliações do usuário na cidade do local;
  - `distancia`: média, nos locais avaliados pelo usuário, de `exp(−km/τ)`, com haversine. Sem coordenada: média das coordenadas da cidade; sem as duas, 0.
- [x] **Previsão de nota:** escore do local + viés do usuário (regularizado, `reg = 10`), limitada a [1, 5]. Sem histórico: só o escore.
- [x] **Testes à mão** de cada componente, inclusive local sem avaliações, cidade pequena, pesos opostos, só notas 3 e distância conhecida.

### 3.3 Pontuação e escolha dos hiperparâmetros (cenário 1)

`s(u,i) = α·sim(u,i) + β·escore_i + γ·local_u(i) + δ·pop_i`, com `sim = (cos + 1) / 2`, pesos ≥ 0 e soma 1.

**Critério, decidido pela usuária:** entre as combinações com `Conversao@10` ≥ 95% da melhor, a de maior AUC de gosto. Reporte sempre a cobertura. **Exija `α ≥ 0,1`**, porque a técnica é baseada em conteúdo, e mostre à parte o melhor com `α = 0`.

Em etapas, salvando cada grade em arquivo, com uma opção para reaproveitar o resultado sem recalcular. Rode em segundo plano: na tentativa anterior, a grade de 286 combinações levou ~3,6 minutos com a conversão e ~14 ao somar AUC de gosto e correlação. Correlação só para os finalistas.

- [x] **Etapa 1, local:** com pesos 0,1 / 0,2 / 0,5 / 0,2, comparar `cidade`, `distancia` (τ de 10 a 400 km) e a média das duas, só como orientação: com pesos fixos, τ maior achata o local e o critério sempre o prefere.
- [x] **Etapa 2, local e pesos em conjunto:** grade com passo 0,1 (286 combinações) para `cidade` e `distancia` com τ = 50, 100, 200, 400 e 800 km, aplicando o critério ao conjunto. Em empate com a melhor combinação usando cidade, ficar com cidade, mais simples de explicar. Referência: 0,1 / 0,2 / 0,5 / 0,2.
- [x] **Etapa 3, refinamentos, um por vez:**
  - `m`: percentis 25, 50 e 75;
  - centro: 3 × média do usuário (a média teve AUC de gosto maior e conversão menor);
  - blocos: só categorias; só atributos; os dois, com atributos em peso 0,5 ou 1;
  - conferência das exclusões: incluir atributos derivados e preço só para medir o quanto se abre mão. Manter fora, salvo ganho claro, e levar à usuária se a diferença for grande.
- [x] **Etapa 4:** se a etapa 3 mudou algo, refinar os pesos em torno do escolhido (±0,1, passo 0,05). Congelar.
- [x] **Ablação:** cada componente sozinho; o modelo sem cada um; `α = 0`, com intervalos. Figura `32_ablacao`.
- [x] **Fronteira:** figura `31_grade_pesos`, com conversão e AUC de gosto em gráficos separados, marcando a combinação escolhida e quanto de conversão custa cada ganho de gosto.
- [x] **Sensibilidade:** limiar de 90% e 97%; usuários com ≥ 1 avaliação no treino.

### 3.4 Implementação do recomendador

- [x] Classe do recomendador, que recebe pesos, `m`, centro, tipo de local e τ, com as operações:
  - ajustar com avaliações de treino, locais, vetorizador e matriz;
  - obter os componentes e pontuar para usuários e locais, em lote;
  - prever nota;
  - explicar uma recomendação: local bem avaliado (nota ≥ 4) mais parecido e os 3 tokens que mais pesam;
  - recomendar para usuário com histórico: abertos não avaliados, com componentes e explicação;
  - recomendar para usuário novo (3.5);
  - usuários para um local novo e posição de um local novo na lista de um usuário (3.6).
- [x] Usuário com 1 ou 2 avaliações usa o mesmo fluxo do usuário antigo.
- [x] **Explicação legível:** dicionário que traduz tokens para português (`misc=service_options:delivery` → "Entrega"), usado pela interface. Tokens sem tradução não aparecem.
- [x] **Testes à mão:** fórmula da pontuação; fechados e avaliados fora da lista; usuário inexistente gera erro; explicação.

### 3.5 Cenário 2: usuário novo

**Protocolo:** usuários `novo` no alvo com ≥ 2 avaliações. Ordenadas por data, a **primeira** simula o cadastro; as demais são o alvo. O cadastro informa a cidade e, conforme o método, as categorias ou o próprio local como exemplo. Esse local sai da lista.

- [x] Comparar pelas métricas da aula:
  1. popularidade global;
  2. escore global;
  3. escore + popularidade, sem informação alguma;
  4. local declarado + escore + popularidade;
  5. o 4 + categorias declaradas, com peso 0,05, 0,1 e 0,2;
  6. o 4 + um local de exemplo, por similaridade de conteúdo, com peso 0,05, 0,1 e 0,2.
- [x] Escolher os pesos pelo mesmo critério. **Decidido pela usuária em 2026-11-04:** as categorias declaradas entram com peso de 0,05, não como filtro.
- [x] **Regra de não esvaziar:** preferências e filtros nunca deixam a lista vazia. Com menos locais que o pedido na cidade, ampliar por distância e avisar. O filtro de preço é ignorado se sobrar pouco.
- [x] Cobertura do espaço de usuários: esperado 100%, inclusive para quem não informa nada.

### 3.6 Cenário 3: local novo para usuário antigo

Modelo treinado no treino do cenário 3, com vetorizador ajustado nele. Local novo: `escore = C`; popularidade = mediana da cidade.

**Separar os resultados por origem** (natural e simulado).

- [x] **Ordenar locais novos para um usuário:** usuários antigos com conversão em local novo; ordenar todos os locais novos abertos. **AUC de consumo** (principal) e `Conversao@10`. Referências: aleatório e só local. `α·sim + γ·local`, com `α` em 0, 0,05, 0,1, 0,2 e 0,3. Escore e popularidade quase não variam entre os novos, por isso ficam de fora aqui.
- [x] **Saída A, local → usuários:** para cada local novo, ordenar os usuários antigos; AUC dos que o avaliaram bem × demais.
- [x] **Saída B, usuário → local:** posição do local novo entre todos os candidatos do usuário, e decisão de recomendar se entrar no top-N. É a forma literal do enunciado.
- [x] **Cobertura do catálogo restrita aos locais novos:** com que frequência entram no top-10? **Se for quase zero, avaliar uma cota de novidade na lista, decidir na validação e avisar a usuária.**
- [x] Cobertura do espaço de itens novos: conteúdo × vizinhos por item.
- [x] Cadastro manual: mesmos campos do vetor, mais cidade e coordenada opcional.
- [x] Não usar `relative_results`. Registrar por quê.

### 3.7 Referências

Fora da técnica escolhida, para mostrar o que se ganha e o que se perde.

- [x] Popularidade; popularidade + local (é também a lista óbvia da serendipidade).
- [x] Vizinhos por item, com cosseno em matriz binária: sozinho e combinado (peso 0,2, com local, escore e popularidade). Na tentativa anterior, usar só a presença da avaliação foi melhor que usar a nota.
- [x] PageRank personalizado no grafo usuário–local, com reinício 0,5. Foi o concorrente de técnica única mais forte.
- [x] Registrar na conclusão por que a técnica foi mantida: atende os 3 cenários sozinha; cobertura de itens novos; o enunciado pede uma técnica.

### 3.8 Previsão de nota

- [x] MAE, MSE e RMSE de: média global; escore; escore + viés. Em avaliações de usuários antigos em locais do treino. Correlação de rankings dos finalistas.

### 3.9 Notebook `03_modelo.ipynb`

- [x] 1. **Teoria (slide d),** com fórmulas: filtragem baseada em conteúdo, TF-IDF, cosseno, perfil ponderado pela nota, média bayesiana, popularidade, local, combinação linear; por que ordenar em vez de prever nota.
- [x] 2. Métricas e protocolos, em uma tabela.
- [x] 3. Componentes: figura `30_escore_bayesiano` (média simples × escore, cor = nº de avaliações); dois usuários reais anonimizados como "Usuário A/B", com histórico, tokens do perfil e top-10 explicado.
- [x] 4. Escolha dos hiperparâmetros. 5. Ablação. 6. Cenário 2. 7. Cenário 3. 8. Referências. 9. Previsão de nota.
- [x] 10. **Congelamento:** tabela com todas as decisões, gravada em `modelos/configuracao.json`. Reajuste em `treino_total` e no treino final do cenário 3, e gravação dos modelos.
- [x] **Ponto de decisão com a usuária antes da Fase 4:** apresentar os hiperparâmetros, o efeito do conteúdo e a comparação com as referências. Depois disso, o teste só roda uma vez.

**Pronto quando:** os 3 cenários funcionam com exemplos, a configuração está congelada, a usuária viu os resultados e o relatório cobre teoria e estimação (slides d, g).

---

## Fase 4 — Avaliação final: `04_avaliacao.ipynb`

**Só carrega a configuração e os modelos. Nenhuma decisão aqui. Roda uma vez** (regra 5).

- [x] 1. Definição das métricas e conferência da configuração.
- [x] 2. **Cenário 1:** modelo × aleatório, popularidade, só escore, só local, popularidade + local, sem conteúdo, vizinhos por item e PageRank personalizado. Todas as métricas da seção A.3, com intervalos. Sensibilidade: usuários com ≥ 1 avaliação no treino. Figura `40_cenario1`.
- [x] 3. **Cenário 2:** os métodos da seção 3.5. Figura `41_cenario2`.
- [x] 4. **Cenário 3:** naturais como principal, simulados à parte; saídas A e B; cobertura do espaço de itens. Figura `42_cenario3`.
- [x] 5. **Curvas ROC:** de gosto (cenário 1) e de consumo (cenário 3). Figura `43_curvas_roc`.
- [x] 6. **Previsão de nota:** MAE, MSE, RMSE; correlação de rankings.
- [x] 7. **Qualidade da lista:** novidade, serendipidade, diversidade, cobertura do catálogo e dos espaços. Dois exemplos: recomendado × avaliado no teste.
- [x] 8. **Estabilidade temporal:** conversão do cenário 1 no primeiro ano do teste (pandemia) × depois.
- [x] 9. **Validação × teste:** as duas métricas principais, lado a lado.
- [x] 10. **Conclusões e limitações, obrigatórias:**
  - conversão offline é aproximação: local não avaliado pode ser só desconhecido;
  - a medida favorece popularidade e proximidade;
  - o sinal de gosto vem da qualidade do local, com pouca personalização;
  - AUC de gosto usa só usuários com notas boas e ruins no período;
  - metadados são de 2021; locais simulados são mais fáceis que os novos reais;
  - fechados são conhecidos por metadado de 2021, o que atinge todos os modelos igualmente;
  - pandemia no teste; coleta rarefeita no fim;
  - vizinhos por item convertem mais para usuários antigos, e por que a técnica foi mantida.

**Pronto quando:** todas as tabelas e figuras existem e o relatório traz os resultados sem suavizar nada (slide h).

---

## Fase 5 — Interface: `app.py` (Streamlit)

- [x] Carregar os modelos com cache. Barra lateral: descrição do sistema e tamanho da lista (5 a 20).
- [x] **Aba 1, usuário antigo:** busca por id e botão "sortear"; mostrar como "Usuário #N", sem nomes de pessoas. Histórico, resumo do perfil em texto legível e cidades. Top-N com nome, cidade, categorias, barras dos componentes e explicação ("porque você gostou de X").
- [x] **Aba 2, usuário novo:** formulário com cidade, categorias, atributos, preço (filtro) e local de exemplo, todos opcionais. Top-N e o que foi usado. Regra de não esvaziar.
- [x] **Aba 3, local novo:** escolher dos locais novos ou cadastrar: nome, cidade, categorias, atributos declaráveis e coordenada opcional. Mostrar (A) top-N usuários e por quê; (B) para um usuário escolhido, a posição na lista e a decisão de recomendar ou não.
- [x] Mensagens para usuário inexistente, formulário vazio e cidade sem locais.
- [x] Configurar `.claude/launch.json` e testar os 3 cenários no painel do navegador, com casos reais. Salvar as telas em `figuras/50_`, `51_` e `52_`. Se não for possível salvar a captura, pedir os prints à usuária.
- [x] **Aba Demonstração** (pedida pela usuária em 2026-11-05): usuário sorteado ou escolhido, gráficos do gosto e das notas, mapa e recomendações em prateleiras de cartões, no estilo de catálogo. As telas passaram a ser `50_` (demonstração) a `53_` (local novo).

**Pronto quando:** os 3 cenários rodam sem erro e as telas estão salvas (slide i).

---

## Fase 6 — Apresentação: `scripts/gerar_ppt.py`

Antes: resolver P1 e P3. Carregar a skill de PPT. O enunciado pede ppt, então o formato é `.pptx`.

Cerca de 20 a 25 slides. Números lidos das saídas dos notebooks.

- [ ] **a.** Capa: título, disciplina, professor, integrantes, data. Falta só o nome dos integrantes (P1).
- [x] **b.** Sistema (2): problema, técnica, fluxo dados → features → perfil e escores → ordenação → interface; os 3 cenários.
- [x] **c.** Base (5–6): origem e recorte; números; notas; atividade; cauda longa; mapa; tempo e sazonalidade.
- [x] **d.** Teoria (3–4): conteúdo, TF-IDF, cosseno; perfil; escores; local; combinação. Justificativa da técnica com as análises da seção 1.5.
- [x] **e.** Tratamento (2): funil; recorte pela categoria principal; atributos excluídos e por quê.
- [x] **f.** Treino e teste (2): divisão temporal com um ano de validação; segmentos; locais novos naturais e simulados.
- [x] **g.** Estimação (2–3): critério duplo e fronteira conversão × gosto; pesos; ablação; exemplo explicado.
- [x] **h.** Performance (4): um slide por cenário, só com métricas da aula e intervalos; previsão de nota e curvas ROC; limitações.
- [x] **i.** Interface (3): uma tela por cenário.
- [x] Encerramento: conclusões, limitações, trabalhos futuros.
- [x] Notas do orador em todos os slides.
- [x] **Revisão visual:** converter para imagens e olhar cada slide. **Busca final:** nenhum slide cita Recall, HitRate, nDCG, MAP ou Precision.

---

## Fase 7 — Entrega

- [ ] `requirements.txt` com as versões das bibliotecas usadas.
- [ ] `README.md`: objetivo, fonte da base, estrutura, ordem de execução (`01 → 02 → 03 → 04 → app`), tempo aproximado.
- [ ] Rodar tudo do zero em sequência e conferir que os números do PPT batem. O notebook 04 aqui só reproduz o resultado, sem decisão nova.
- [ ] Rodar todos os testes.
- [ ] Resolver P4 e montar a pasta de entrega.
- [ ] Revisão final contra o enunciado: seções a–i, os 4 entregáveis, ratings por usuário, originalidade, base no Moodle. Busca em todo o projeto por métricas fora da aula.

---

## Riscos

| Risco | O que fazer |
|---|---|
| A validação de um ano deixa o treino pequeno | Conferir o mínimo da seção 2.2; se faltar, usar uma validação menor, considerando a sazonalidade, e registrar |
| O recorte novo muda os achados | Os números deste plano são só referência. Reavaliar as decisões afetadas (regra 2) |
| Distância não ganha de cidade com pesos refinados | Manter cidade |
| Local novo quase nunca entra nas listas | Avaliar cota de novidade, com a usuária (seção 3.6) |
| Atributos declaráveis pioram o cenário 3 de forma relevante | Medir na etapa 3 e levar à usuária |
| Definições diferentes nos slides da disciplina | Ajustar as métricas antes de escolher os pesos (P2) |
| Grade lenta | Salvar resultados, usar amostra de usuários só para explorar, segundo plano |
| Modelo perde para referência no teste | Reportar e discutir (regra 9) |

---

## Diário de execução

> A cada sessão: data, fase, o que foi feito, números, decisões, desvios e próximo passo.

- **2026-11-03 — Plano criado para recomeçar do zero.** Técnica, métricas e critério definidos pela usuária na tentativa anterior, cujos arquivos foram apagados. Próximo: Fase 0.
- **2026-11-03 — Fase 0, falta só P5.** A pasta tinha apenas os quatro arquivos esperados. Python 3.14.7 e todas as bibliotecas da regra 12 já instaladas, nada foi instalado; um notebook de teste no scratchpad importou tudo e rodou pelo nbconvert. Criados `src/` (com `__init__.py`), `testes/`, `data/processed/`, `modelos/`, `figuras/` e `relatório.md`. **Desvio:** os JSON estão na raiz, não em subpastas; A.4 e Parte C corrigidas. **Em aberto:** P5, que depende da resposta da usuária, e o ajuste da inclusão manual da seção 1.2 (incluir os locais específicos, não as categorias Dinner theater e Concert hall), a confirmar na inspeção da Fase 1. Próximo: resolver P5 e iniciar a Fase 1.
- **2026-11-03 — Fase 0 concluída.** P5 resolvida: a usuária confirmou que a base já foi publicada no Moodle. Próximo: Fase 1.
- **2026-11-03 — Seção 1.1 concluída.** `src/dados.py` tem `ler_metadados` e `ler_avaliacoes`; 7 testes passam; `01_dados.ipynb` executado sem erro. Lidas 12.088 linhas de metadados (12.016 `gmap_id` distintos) e 1.141.421 avaliações, todas de locais presentes nos metadados, das quais 17.050 sem `rating` e 17.050 sem `user_id`. **Provisório:** como o recorte ainda não existe, o notebook lê as avaliações de todos os locais; a seção 1.2 troca essa seleção pelos locais de gastronomia. **Para a seção 1.3:** `state` está nulo ou ausente em 4.623 locais (1.122 sem a chave), o que não pode ser lido como fechado; conferir se os nulos de `rating` e `user_id` são as mesmas linhas. Próximo: seção 1.2.
- **2026-11-03 — Seção 1.2 concluída.** Recorte com 1.863 locais e 433.918 avaliações brutas: 1.855 locais (431.165 avaliações) pela regra e 8 (2.753) pela inclusão manual. Referência: ~1.857 e ~429 mil. Hotéis, truck stops, mercados, livrarias, boliches e postos ficaram fora. 34 testes passam e o notebook roda sem erro. **Desvios:** (1) a inclusão manual virou lista de `gmap_id`, não de categorias; além dos dois exemplos do plano, a inspeção acrescentou 6 locais. (2) Alf's Pub, Saddle Lite Saloon, Pizza Ranch FunZone Arcade e Black Gold Grille ficaram fora, pois suas categorias descrevem outro negócio e gerariam vetor de conteúdo enganoso. (3) O notebook agora conta as avaliações do arquivo inteiro em uma passada e só carrega as do recorte; por isso as contagens de nulos, fotos e respostas passaram a ser do recorte. **Achado para a seção 1.3:** nenhuma das 17.050 avaliações sem `rating` do arquivo inteiro está no recorte, contra ~1,3 mil na referência; a etapa pode remover zero linhas. Próximo: seção 1.3.
- **2026-11-03 — Seção 1.3 concluída.** Ficaram 429.622 avaliações e 1.863 locais em `data/processed/`. Removidas 4.296 duplicatas exatas; nenhuma sem nota ou usuário e nenhuma repetição depois das duplicatas. 52 testes passam; duas execuções geraram parquets com o mesmo sha256. Números do recorte: 177.267 sem texto (41,3%), 3.290 traduzidos, 7 locais sem cidade (6 sem endereço, todos com coordenada), 6 sem CEP, 16 com `₩`, 205 fechados permanentes e 33 temporários, correlação de 0,991 com `avg_rating`. **Desvios das referências:** nenhuma coordenada anulada, pois o Grasslands Market não está no recorte; 7 sem cidade, contra ~38. **Decisão:** as rajadas (5.832 avaliações, 1,4%; 993 rajadas, 21,0% com nota constante, contra 11,7% fora delas) ficam todas, inclusive as de nota constante, que o plano não definia: somam 1.199 avaliações, só 5 rajadas repetem texto e há menos notas 5 que fora delas. `time` foi substituído por `data`. Próximo: seção 1.4.
- **2026-11-03 — Seção 1.4 concluída.** 175.278 usuários, 1.863 locais, 115 cidades, nota média de 4,15 (desvio de 1,21), esparsidade de 99,868%, 78,1% das notas ≥ 4, Gini de 0,587. Figuras `10_` a `19_` e `1a_`, conferidas uma a uma. 54 testes passam; o notebook roda sem erro e os parquets não mudaram. **Mudança nos achados:** 66,0% dos usuários têm uma única avaliação (B.1 dizia cerca de metade), reforçando o cenário 2; usuários com ≥ 3 são 19,9% e têm 61,6% das avaliações. **Desvio:** o gráfico de meses usa 2017 a 2019, pois no período inteiro a pandemia e o fim da coleta distorcem a sazonalidade (julho/fevereiro de 2,05 contra 1,45; turísticas, 3,29 contra 2,34). **Criado:** `src/graficos.py`, com o estilo único. O plano continua de pé. Próximo: seção 1.5.
- **2026-11-03 — Seção 1.5 concluída; Fase 1 pronta.** Corte de teste em 31/03/2020 (343.697 avaliações antes, 85.925 depois); corte de validação em 31/03/2019, com treino de 213.626 e validação de 130.071, acima do mínimo de 150 mil. `src/analises.py` e testes criados; 69 testes passam; notebook roda sem erro. **Técnica mantida.** **Efeito do recorte:** local explica 11,5% da nota (~11%); local + usuário entre quem tem ≥ 5, 36,6% brutos e 29,6% ajustados (~35%); estabilidade de 0,833 (~0,79); nota × popularidade de −0,128 (~−0,16); cidade principal de 75,0% (~79%); cidade nova em 24,1% (~22%); nota ≥ 4 em 77,6% (~78%); notas constantes em 11,1% (~12%); 20º vizinho com 4 e 9 em comum (~4 e ~10); Jaccard de 0,0878 × 0,0964 (~0,081 × ~0,091); usuários novos de 51,1% a 57,4% (~60%); locais novos de 1,8% a 2,7% (~4%). **Mudanças no plano:** (1) A.3 dizia 85% de consumo com nota ≥ 4; o medido é cerca de 78%. (2) Etapa 1 da Fase 3 ganhou τ = 10 km, pois 77,9% das avaliações ficam a até 10 km do local mais próximo e a curva quase para até 50 km. (3) A seção 2.1 ganhou a revisão dos valores declaráveis, pois os atributos declaráveis se correlacionam com a popularidade tanto quanto os derivados (0,596 × 0,492) e Planning inclui valores de comportamento. (4) A curva de distância é acumulada, não histograma, por ser mais legível com a distribuição em dois grupos. **Análise não prevista:** decomposição ajustada, porque o valor bruto de local + usuário (64,6%) é inflado por usuários com uma só avaliação. Próximo: Fase 2.
- **2026-11-03 — Seção 2.1 concluída.** `src/features.py` e `testes/test_features.py` criados; 106 testes passam; `02_preparacao.ipynb` criado e executado sem erro. **Revisão de valores:** dos 47 valores declaráveis, 4 excluídos (`Usually a wait`, `Quick visit`, `Curbside pickup`, `No-contact delivery`) e 11 grafias unificadas. **Achado:** os metadados também denunciam quem continuava aberto em 2021, por exemplo `Takeout` em 85,4% dos abertos e 27,8% dos fechados; esses valores ficam, com limitação declarada. **Conferência:** ajustado com os 1.647 locais do treino, o vetor tem 167 tokens (136 de categorias e 31 de atributos) para os 1.863 locais; um local tem vetor vazio (Gillette Cheese House, categoria `Food`, fora do vocabulário do treino). A Fase 3 precisa tratar vetor vazio como similaridade neutra. Próximo: seção 2.2.
- **2026-11-03 — Seção 2.2 concluída.** `src/divisao.py` e `testes/test_divisao.py` criados; 113 testes passam; notebook roda sem erro. Corte de teste em 31/03/2020 e de validação em 31/03/2019. Treino: 213.626 (mínimo de 150 mil atendido; 77,1% relevantes). Validação: 130.071 (78,5% relevantes). Treino total: 343.697 (77,6% relevantes). Teste: 85.925, só com datas e contagens. **Desvio:** a tabela de partições não mostra % de relevantes do teste, para não calcular nada ligado às notas antes da Fase 4; seção 2.4 ajustada. **Limitações registradas:** 86,2% do teste no primeiro ano depois do corte (pandemia), enquanto a validação é quase toda anterior a ela; 1,3% do teste a partir de junho de 2021. Gravar as partições fica para a seção 2.3, e a figura `21_divisao_temporal`, para a 2.4. Próximo: seção 2.3.
- **2026-11-03 — Seção 2.3 concluída.** `src/divisao.py` ampliado; 123 testes passam; notebook roda sem erro; duas execuções geraram arquivos com o mesmo sha256. Gravados em `data/processed/conjuntos/`: as 4 partições, `treino_c3`, `treino_total_c3`, `locais_novos`, `indice_locais` e `divisao.json`. **Segmentos:** validação com 25,5% antigos, 14,5% intermediários e 60,0% novos; teste com 25,7%, 12,8% e 61,5% (só contagens). **Locais novos:** naturais 113 na validação (106 abertos) e 103 no teste (100 abertos); simulados 100 e 100, todos abertos, sem nenhum em comum. **Treinos do cenário 3:** 196.785 (16.841 a menos) e 318.092 (25.605 a menos). **Atenção:** os naturais têm só 1.357 avaliações de antigos na validação e 951 no teste, então os intervalos do cenário 3 devem ser mais largos. **Detalhes:** as partições não guardam o texto das avaliações, que não é usado no modelo; as colunas `_c3` trazem o segmento conforme o treino do cenário 3. **Desvio de execução:** as células foram acrescentadas por um script que confere a célula-âncora, sem gerar o notebook do zero. Próximo: seção 2.4.
- **2026-11-03 — Seção 2.4 concluída; Fase 2 pronta.** 124 testes passam; notebook roda sem erro; as 17 verificações automáticas passam; arquivos gravados inalterados. **Conteúdo:** 226 categorias viram 136 com o `min_df`, 31 atributos ficam; matriz de 1.863 × 167, esparsidade de 94,0%, mediana de 9 tokens por local. **Sanidade:** 79,7% dos 5 vizinhos têm a mesma categoria principal (5,7% ao acaso) e 98,1% têm alguma categoria em comum; só com categorias, 77,9% e 99,4%, então os atributos reduzidos não pioraram. Figuras `20_vizinhos_conteudo` e `21_divisao_temporal` conferidas; a primeira precisou de correção, pois locais de mesmo nome viravam uma barra só. **Limitação:** o cosseno mede tipo, não qualidade (o Million Dollar Cowboy Bar fica a 0,959 de um bar de Farson). **Desvio de execução:** células acrescentadas por script que confere o conteúdo; as tabelas de partições, segmentos e locais novos ficaram nas seções 2.2 e 2.3, sem repetição. O plano continua de pé. Próximo: Fase 3, começando por resolver a pendência P2 com a usuária.
- **2026-11-03 — P2 resolvida.** A usuária decidiu usar as definições de cobertura, novidade e serendipidade da seção A.3, sem conferir nos slides da disciplina. Os slides devem declarar que elas vêm da literatura geral. Próximo: restante da seção 3.1.
- **2026-11-03 — Seção 3.1 concluída.** `src/metricas.py` e `testes/test_metricas.py` criados; 155 testes passam; `03_modelo.ipynb` criado e executado sem erro. **Conferência na validação (não decide nada):** 6.078 usuários antigos e 1.419 candidatos. Aleatória: conversão@10 de 0,0028, contra 0,0029 esperados ao acaso; AUC de gosto de 0,4973; AUC de consumo de 0,5016. Popularidade: conversão@10 de 0,0204, AUC de gosto de 0,4858 (empate com a aleatória), AUC de consumo de 0,7394 e cobertura do catálogo de 1,3%. **Atenção:** a AUC de gosto vale só para 2.397 dos 6.078 usuários, os que têm notas boas e ruins no período. **Detalhes de implementação:** empates desfeitos por um ruído mínimo sorteado (amplitude de 1e-9); `NaN` marca par não pontuável; novidade conta local sem avaliação como tendo uma, para não dividir por zero; `pares_excluidos` atende o cenário 2. Próximo: seção 3.2.
- **2026-11-03 — Seção 3.2 concluída.** Componentes em `src/recomendador.py`; testes em `testes/test_recomendador.py`; 179 testes passam; notebook roda sem erro. **No treino:** `C` = 4,116; `m` = 75; 216 locais sem avaliação; 62 locais com média 5 têm mediana de 3 avaliações e escore de no máximo 4,413; maior escore aberto de 4,687; priores de cidade de 3,546 a 4,554; 95.365 perfis, 5.384 só com notas neutras e 5 com vetor nulo; popularidade mediana de 0,620 nos locais sem avaliação e 0,600 nos avaliados; viés de −1,382 a 0,793. **Para a seção 3.3:** cidade e distância têm correlação de 0,958 (τ = 25 km), então um empate é provável, e fica com cidade, como previsto. Os componentes têm espalhamentos muito diferentes (desvio-padrão de 0,054 no escore, 0,095 na similaridade, 0,179 na popularidade e 0,220 no local), então peso maior não significa importância maior; os pesos são lidos pelo efeito nas métricas, e a escala dos componentes não foi alterada, para manter o plano. Nenhuma métrica foi calculada com os componentes. Próximo: seção 3.3.
- **2026-11-04 — Seção 3.3 concluída.** 191 testes passam; notebook roda sem erro. **Congelado em `modelos/cenario1.json`:** distância com τ = 200 km, `m` no percentil 25 (m = 26), centro pela média do usuário, categorias + atributos e pesos 0,1 / 0,2 / 0,5 / 0,2. **Na validação:** conversão@10 de 0,0739 (IC 95% de 0,0713 a 0,0766), AUC de gosto de 0,5850 (IC 95% de 0,5721 a 0,5981; 2.397 usuários), cobertura do catálogo de 45,9%. **Mudança no plano:** na etapa 1 com pesos fixos, τ = 100 km e depois τ = 400 km venceram no limite do que foi testado, pois τ maior achata o local e favorece o escore. Por isso, local e pesos passaram a ser escolhidos em conjunto, com 6 grades de 286 combinações; τ = 800 km quase nunca passa do limite, o que fecha o intervalo. **Ressalva:** a escolha conjunta foi feita antes de `m` e centro; com a configuração final e pesos fixos, o critério apontaria τ = 400 km (0,0716; 0,5913; cobertura de 39,5%), comparação que tem o mesmo problema e não foi seguida. **Achados para a usuária:** (1) sem conteúdo, a conversão é maior (0,0015, IC 95% de 0,0005 a 0,0024) e a AUC de gosto empata, então no cenário 1 o conteúdo só amplia o catálogo (45,9% × 40,8%) e `α` fica no mínimo exigido; o melhor com `α = 0` empata na conversão e tem AUC maior (0,0089); (2) o sinal de gosto vem do escore, e sem ele a AUC cai para 0,4847; (3) a escolha depende do limiar (90%: 0,1 / 0,3 / 0,4 / 0,2; 97%: 0,1 / 0,1 / 0,6 / 0,2). **Exclusões:** derivados rendem 0,0042 de AUC, ganho pequeno, então seguem fora; preço empata. **Blocos:** "só categorias" empata, mas numa rodada descartada (τ = 400 km) ela chegou a vencer por pouco, então essa escolha é frágil; rever no cenário 3. **Sensibilidade:** usuários com 1 ou mais avaliações escolhem os mesmos pesos. **Correção de execução:** o nome das grades passou a incluir a configuração, para não reaproveitar uma grade de outra. Células acrescentadas por script que confere o conteúdo. Próximo: seção 3.4.
- **2026-11-04 — Decisão da usuária:** manter o conteúdo com peso de 0,1 no cenário 1, mesmo sem ganho nas métricas principais.
- **2026-11-04 — Seção 3.4 concluída.** Classe `Recomendador` em `src/recomendador.py` e dicionário em `src/traducoes.py` (172 tokens); `calcular_componentes` passou a usar a classe; 210 testes passam; notebook roda sem erro, com os mesmos resultados da seção 3.3. **Conferência:** pontuações idênticas às da etapa anterior; 167 tokens do vetor, nenhum sem tradução; lista com explicações em 0,13 s; em 100 usuários e 1.000 recomendações, nenhum fechado ou já avaliado na lista e 99,0% das explicações com local parecido. **Provisório:** `recomendar_usuario_novo` usa os pesos do cenário 1, sem a regra de não esvaziar nem filtro de preço (seção 3.5); `pesos_local_novo` vale (0,1; 0,5) até a seção 3.6, e a interface da Fase 5 trata as mensagens. **Limitações:** a lista é pouco pessoal, com sobretudo locais populares e bem avaliados da região; "porque você gostou de X" é uma justificativa, não a causa, pois local e popularidade pesam mais na posição, então a interface deve mostrar as barras dos componentes. Próximo: seção 3.5.
- **2026-11-04 — Repositório criado.** Privado, em https://github.com/Chelughini/sistema-recomendacao-t1, a pedido da usuária. Fora dele: os JSON brutos, pois `review-Wyoming.json` passa do limite de 100 MB, e `data/`, que tem identificadores de usuários e comentários e é regenerada pelos notebooks. Os notebooks não têm identificadores de usuários nas saídas. Um `README.md` curto foi antecipado, para explicar como obter os dados; a Fase 7 o completa. O envio usa HTTPS, pois o SSH desta máquina não está configurado para o GitHub. Próximo: seção 3.5.
- **2026-11-04 — Seção 3.5 quase concluída; falta a decisão da usuária.** Neste computador, os dados foram baixados da UCSD e as bibliotecas que faltavam foram instaladas; os notebooks 01 e 02 regeneraram `data/processed/` com os mesmos números (só os sha256 e os metadados das figuras mudaram, pela versão do pyarrow e do matplotlib). Criados `simular_cadastros` (`src/divisao.py`) e, na classe `Recomendador`, `componentes_cadastros`, `coincidencia_de_categorias` e a regra de não esvaziar em `recomendar_usuario_novo` (filtro de categorias que completa a lista, filtro de preço ignorado se sobrar pouco, aviso de cidade pequena, avisos em `tabela.attrs`). 220 testes passam; o notebook roda sem erro, com as células antigas iguais, salvo os tempos. **Protocolo:** 45.530 novos na validação, 12.037 com 2 ou mais avaliações, 10.000 no protocolo, 2.254 com AUC de gosto. **Números:** método 4 (0 / 0,2 / 0,5 / 0,3) converte 0,0484 com AUC de gosto de 0,5539 e cobertura de 27,9%; popularidade global, 0,0129; escore sozinho, AUC de 0,6905 e conversão de 0,0022. Categorias com α = 0,05 empatam nas duas métricas (cobertura de 31,8%); α = 0,1 perde 0,0006 de conversão; α = 0,2 perde as duas. Local de exemplo com α = 0,05 e 0,1 empata; α = 0,2 perde gosto. **Categorias como filtro** derrubam a conversão para 0,0239 e o gosto em 0,0501, porque só 18,8% do alvo tem a categoria declarada (12,1% ao acaso). O critério aponta categorias com α = 0,05. **Desvios:** (1) a categoria declarada na simulação é a principal do primeiro local; (2) os métodos 3 e 4 tiveram os pesos escolhidos em grade (11 e 66 combinações), e os métodos 5 e 6 usam os pesos do 4 multiplicados por `1 − α`; (3) o filtro de categorias foi medido como alternativa, para embasar a decisão pendente. **Em aberto:** decisão da usuária sobre o modo das categorias e o peso único do conteúdo declarado; depois, gravar os pesos do usuário novo na classe. Próximo: essa decisão e, então, a seção 3.6.
- **2026-11-04 — Decisão da usuária e seção 3.5 concluída.** As categorias declaradas entram com peso de 0,05, não como filtro; o peso vale para todo o conteúdo declarado. Congelado em `modelos/cenario2.json` e em `PESOS_USUARIO_NOVO` da classe: 0,05 / 0,19 / 0,475 / 0,285. Na validação: conversão@10 de 0,0484 (IC 95% de 0,0469 a 0,0499) e AUC de gosto de 0,5541 (IC 95% de 0,5384 a 0,5696). **Limitação:** a categoria quase não muda a lista (Cheyenne + restaurante chinês dá um chinês, em 8º). A regra de não esvaziar foi conferida no caso extremo (Moran, pizza, preço 4): 10 locais, com os avisos. Os avisos passaram a usar singular e plural. Próximo: seção 3.6.
- **2026-11-04 — Seção 3.6 concluída.** Modelo no treino do cenário 3 (196.785 avaliações; C = 4,114; m = 25). Naturais: 106 abertos, 857 usuários com conversão; simulados: 100 e 1.553. **Mudança de rumo, decidida pela usuária:** com o perfil do cenário 1 (centro na média do usuário), o conteúdo piorava a ordenação dos locais novos, e sozinho ficava quase no acaso (AUC de consumo de 0,5107); com o perfil centrado em 3, ele sobe para 0,6351 e passa a ajudar. O cenário 3 usa o perfil centrado em 3 (`centro_local_novo`), e o cenário 1 segue com o da média. **Ordenar locais novos (naturais):** só local, AUC de consumo de 0,9195 e conversão@10 de 0,0877; α = 0,5, 0,9314 (+0,0119, IC 95% de 0,0074 a 0,0163) e 0,0939. O critério (conversão ≥ 95% da melhor, depois a maior AUC de consumo) escolhe α = 0,5, em empate com 0,1 a 0,4. **Desvio:** a grade do plano (até 0,3) foi ampliada para 0,4, 0,5 e 0,7, pois o critério escolhia o fim dela. **Blocos:** só categorias perde (−0,0050 e −0,0126), então os atributos ficam, o que fecha a dúvida da seção 3.3. **Saída A:** AUC de 0,9176 contra 0,9102 do só local (+0,0074). **Saída B:** com o modelo do cenário 1, o local novo convertido fica em 69º, em mediana; só 3,1% entram no top-10 e 5,7% das listas têm algum local novo. **Cota de novidade, decidida pela usuária:** 1 local novo no top-10; custa 0,0028 de conversão (96% da conversão sem cota) e leva as listas com local novo convertido de 29 para 149 e os locais novos listados de 42 para 95 de 106. Na classe, `recomendar` passou a considerar os 206 locais abertos sem avaliações no treino, com a coluna `novo`. **Cobertura de itens novos:** conteúdo 100%, vizinhos por item 0%. Congelado em `modelos/cenario3.json`. Funções novas em `src/metricas.py`: `auc_por_item`, `posicoes_na_lista`, `top_n_com_novos` e `aplicar_cota_de_novos`. 227 testes passam. Textos da seção 3.4 atualizados, pois os pesos deixaram de ser provisórios. Próximo: seção 3.7.
- **2026-11-04 — Seção 3.7 concluída.** `src/referencias.py` com `VizinhosPorItem` (cosseno na matriz binária, média das similaridades com os avaliados) e `PageRankPersonalizado` (grafo bipartido, reinício de 0,5, forma fechada `q = c·x_u + (1 − c)²·q·M` conferida nos testes contra o passeio no grafo inteiro); 233 testes passam. **Cenário 1, validação:** modelo 0,0739 de conversão@10 e 0,5850 de AUC de gosto; vizinhos 0,0806 e 0,4660; PageRank 0,0831 e 0,4739; vizinhos combinados (0,2 com escore, local e popularidade) 0,0864 e 0,5188; popularidade + local 0,0715 e 0,4796. **Achado para a usuária:** o combinado converte 17% mais que o modelo (+0,0125, IC 95% de 0,0105 a 0,0144), acima dos ~8% da tentativa anterior que embasaram a escolha; pelo critério do projeto ele venceria, e o modelo não passaria do limite de conversão (0,0821). Em compensação, só o modelo tem AUC de gosto acima do acaso entre os fortes, e só ele pontua locais novos. **Técnica mantida** pelas três razões do plano (uma técnica; os 3 cenários; gosto), com a perda de conversão como limitação; a decisão final fica para o ponto de decisão da seção 3.9. Próximo: seção 3.8.
- **2026-11-04 — Seção 3.8 concluída.** Em 31.767 avaliações de 6.660 usuários antigos da validação, em locais do treino: RMSE de 1,0960 (média global), 1,0427 (escore) e 0,9871 (escore + viés); MAE de 0,8576, 0,8225 e 0,7553. Cada passo melhora com intervalo longe de zero (escore − média: −0,0351 de MAE; viés − escore: −0,0672). Os valores ficam perto dos da tentativa anterior (~1,09, ~1,04 e ~0,98). A correlação de rankings dos finalistas já estava na seção 3.3. Próximo: seção 3.9.
- **2026-11-04 — Seção 3.9 concluída, falta o ponto de decisão.** Teoria com fórmulas no início do notebook (conteúdo, TF-IDF, cosseno, perfil com os dois centros, escores, local, combinação, por que ordenar). Figura `30_escore_bayesiano` (escore congelado × média simples, cor = avaliações em escala log): os 194 locais com menos de 10 avaliações vão de 1 a 5 na média e de 3,54 a 4,34 no escore. Exemplos: Usuário A (Cheyenne) e Usuário B (Evanston, 23 avaliações), com histórico, tokens do perfil e top-10 explicado; o exemplo de usuário novo do cenário 2 passou a se chamar Usuário C. **Congelado** em `modelos/configuracao.json`; reajuste em `treino_total` (343.697 avaliações, C = 4,132, m = 36,8, 100 locais novos) e `treino_total_c3` (318.092, 200 locais novos), gravados em `modelos/*.joblib` (122 e 115 MB), que ficam fora do git por terem identificadores de usuários (`.gitignore` atualizado). A tabela de métricas já estava na seção de métricas. Próximo: ponto de decisão com a usuária e, depois, a Fase 4.
- **2026-11-04 — Ponto de decisão:** a usuária confirmou a configuração congelada e a técnica, ciente de que os vizinhos combinados convertem 17% mais no cenário 1. Próximo: Fase 4, com o teste rodando uma única vez.
- **2026-11-04 — Fase 4 concluída; o teste rodou uma única vez.** `src/avaliacao.py` (`cenario1`, `cenario2`, `cenario3`, `erros_previsao`, `pares_roc_gosto`, `pares_roc_consumo`) e `testes/test_avaliacao.py`; 238 testes passam. **Ensaio:** as funções foram rodadas antes na validação (script e uma cópia temporária do notebook, apagada) e reproduziram o 03 ao centavo; o ensaio pegou só ajustes de apresentação (período vazio, plural, casas decimais). **Teste:** cenário 1, modelo 0,0520 de conversão@10 e 0,5542 de AUC de gosto (5.663 usuários); empata na conversão com popularidade + local e com sem conteúdo; vizinhos combinados 0,0651 (+25%), todos os colaborativos abaixo do acaso no gosto. Cenário 2, 0,0452 e 0,5598 (6.783 usuários), empate com o método 4. Cenário 3, naturais: AUC de consumo de 0,9209 contra 0,9173 do só local, **empate** (+0,0036, IC de −0,0008 a 0,0076), ao contrário da validação; simulados +0,0044, fora do empate. Cota: listas com local novo convertido de 21 para 126, com −0,0014 de conversão. Previsão: RMSE de 1,0248 (escore + viés). Estabilidade: conversão de 0,0504 no primeiro ano e 0,0235 depois, nas duas ordenações. Figuras `40_` a `43_` conferidas; a curva ROC de gosto tem degraus, explicados na leitura. **Desvios:** (1) o notebook 04 foi criado por um script de uso único, que aborta se o arquivo existir, e as leituras foram acrescentadas por script que confere âncoras; (2) a saída B usa os usuários com conversão entre os candidatos, e não uma amostra de 10.000, e na validação dá 3,4% no top-10, contra 3,1% do notebook 03; (3) os pesos do método 3 do cenário 2 (0 / 0,3 / 0 / 0,7) estão escritos no notebook 04, lidos da saída do 03. Nada foi ajustado depois do teste. Próximo: Fase 5 (interface).
- **2026-11-05 — Fase 5 concluída.** `app.py` com quatro abas (Demonstração, Usuário antigo, Usuário novo, Local novo), `src/interface.py` (numeração "Usuário #N", opções traduzidas de categorias e atributos, resumo e gráfico do perfil, histórico, motivo do cenário 3, prateleiras e cartões) e `testes/test_interface.py`; 251 testes passam. **Pedido da usuária durante a fase:** aba de demonstração com as preferências em gráficos e as recomendações em prateleiras no estilo Netflix; todas as prateleiras saem da pontuação do modelo. **Testes:** painel do navegador e `AppTest` do Streamlit nos três cenários e nas mensagens (usuário inexistente, formulário vazio, regra de não esvaziar, cidade sem locais, cadastro vazio), sem erros. O teste de `prateleiras` pegou o top da demonstração diferente da lista do cenário 1 (a cota valia para as 40 posições da lista ampliada); corrigido. O componente "Local" sobrescrevia o nome do local na tabela e virou "Localização". **Telas:** `figuras/50_` a `53_`, salvas pelo `scripts/capturar_telas.py` (Playwright, tema claro, 1.800 px de largura) com usuários fixos (#12.369 e #70.927). **Desvios:** (1) o painel do navegador leu o `.claude/launch.json` da pasta em que a sessão começou (outro projeto), e o servidor foi iniciado pelo terminal; o `.claude/launch.json` deste projeto ficou criado para as próximas sessões; (2) quatro telas em vez de três, por causa da aba nova. Próximo: Fase 6 (apresentação), que depende de P1 (integrantes e título) e P3 (template).
- **2026-11-05 — Fase 6, base dos slides gerada.** Roteiro em `apresentacao/roteiro_slides.md` (27 slides no completo; versão de 15 minutos com 16 slides e apêndice, a pedido da usuária). `scripts/gerar_ppt.py` (python-pptx) gera `apresentacao/T1_Sistema_Recomendacao.pptx`: 17 slides principais (itens a–i, a demonstração e as conclusões) e 7 de apêndice, com notas do orador em todos. **Visual:** o modelo da usuária no Canva (fundo bege `EDE7DD`, títulos em terracota `B44E1C`, subtítulos em sálvia `697967`, mostarda `CC8B20`, cartões brancos arredondados; capa com o círculo branco e os três traços). As fontes do modelo (Montserrat e Inter) não estão instaladas: os títulos usam Century Gothic e o texto, Arial; no Canva, volta-se às originais. **Demonstração:** incluída a pedido da usuária (slide com o roteiro ao vivo em 3 passos e as telas de reserva); usar ou não ao vivo fica para decidir. **Conferência:** o validador da skill passou; os slides foram renderizados pelo PowerPoint e revisados (corrigidos sobreposições no funil e no roteiro da demonstração, cabeçalhos quebrados na tabela de pesos e telas ilegíveis); nenhuma métrica proibida no texto. **Desvios:** (1) o plano previa o link do Canva, bloqueado no painel do navegador; a usuária mandou o PDF; (2) o deck é uma base para o Canva, e não a versão final. Falta: integrantes (P1) e a decisão sobre a demonstração ao vivo.
- **2026-11-05 — Slides revistos contra o enunciado.** A pedido da usuária, o deck segue os itens a–i na ordem, com um slide de roteiro e o item no rodapé de cada slide. Mudanças: (e) tabela de duplicados e ausentes, com quanto havia e o tratamento de cada um; (g) slide do que foi estimado (C = 4,132, m = 36,8, 140.895 perfis, 167 tokens, τ = 200 km, viés com reg = 10) e os pesos por cenário; (h) as métricas passaram a abrir a performance. **Método didático (d), também a pedido dela:** a ideia em quatro perguntas e cinco passos com exemplo de brinquedo (a usuária fictícia Ana, contas feitas no gerador) e exemplo real do Usuário #12.369 (The Depot Restaurant em 1º com 0,724; Bar J Chuckwagon Suppers, melhor escore da base, em 375º de 1.508 por estar longe), números lidos do `recomendador.joblib` e escritos no gerador. Agora são 24 slides principais e 7 de apêndice; renderizados e revisados, validador sem erros. **Ponto em aberto:** 24 slides para 15 minutos dá cerca de 35 segundos cada.
