# Roteiro dos slides — Trabalho T1

Roteiro da apresentação. A versão de 15 minutos (fim deste arquivo) foi gerada em `apresentacao/T1_Sistema_Recomendacao.pptx` por `scripts/gerar_ppt.py`, como base para os slides finais no Canva. Cada slide traz o **título-mensagem** (o que a plateia deve levar), o **visual**, os **números** e a **fala**, que vira a nota do orador. Os números vêm do `relatório.md`, e as figuras, de `figuras/`.

**Regras que valem para todos:** só as métricas da aula (nada de Recall, HitRate, nDCG, MAP ou Precision); toda comparação com IC 95%, e "empate" quando o intervalo inclui zero; nenhum identificador de usuário; números no formato brasileiro.

**Itens do enunciado → slides:**

| Item | Pede | Slides |
|---|---|---|
| a | Capa com título e integrantes | 1 |
| b | Descrever o sistema | 2–3 |
| c | Base com estatísticas descritivas e gráficos | 4–8 |
| d | Conceitos teóricos do modelo | 9–12 |
| e | Tratamento de dados | 13–14 |
| f | Critérios de treino e teste | 15–16 |
| g | Estimação do modelo | 17–20 |
| h | Performance com as métricas da aula | 21–24 |
| i | Interface funcionando nos 3 cenários | 25–26 |
| — | Encerramento | 27 |

São 27 slides. Para uma apresentação curta, os candidatos a juntar ou ir para o apêndice estão marcados com ◇.

---

## a. Capa

### 1. Capa
- **Título (provisório):** "Onde comer em Wyoming: recomendação por conteúdo e escores de produto"
- Disciplina Sistemas de Recomendação · Prof. Rafael Scopel, PhD · integrantes **[P1]** · data.
- Visual: o mapa dos locais (`16_`) esmaecido como fundo, ou um cartão da demonstração.

## b. O sistema

### 2. Recomendar onde comer a quem avalia no Google, em três situações
- Três cartões, um por cenário: **usuário antigo** (lista pelo histórico), **usuário novo** (lista pelo que a pessoa informa), **local novo** (para quais usuários antigos indicar um local recém-cadastrado).
- Técnica escolhida entre as quatro do enunciado: **conteúdo e escores de produto**.
- Fala: por que os três cenários importam aqui: 66% dos usuários têm uma única avaliação e de 51% a 57% das avaliações vêm de usuários novos.

### 3. Como o sistema decide
- Diagrama de fluxo: avaliações + metadados → vetor de conteúdo (TF-IDF) e escores de cada local → perfil do usuário → pontuação com 4 componentes → lista com explicação → interface.
- Fórmula: `s(u,i) = α·conteúdo + β·escore + γ·localização + δ·popularidade`.
- Fala: cada recomendação vem com o porquê ("porque você gostou de X") e com as barras dos componentes.

## c. A base

### 4. Google Local 2021: 430 mil avaliações de restaurantes, cafés e bares de Wyoming
- Tabela-resumo: 429.622 avaliações · 175.278 usuários · 1.863 locais · 115 cidades · 2008 a 2021 · nota média 4,15 · esparsidade 99,868%.
- Destaque: a base **tem nota por usuário** (exigência do enunciado).
- Fonte: McAuley Lab (UCSD); recorte pela categoria principal de alimentação.

### 5. As notas são altas: 78% são 4 ou 5
- Visual: `10_distribuicao_notas`.
- Números: nota 5 sozinha tem 55,6%. Decisão: **relevante = nota 4 ou mais**.

### 6. Pouco histórico por pessoa, atenção concentrada em poucos locais
- Visual: `11_atividade_usuarios` + `12_popularidade`, lado a lado.
- Números: 66% dos usuários têm 1 avaliação; só 10,4% têm 5 ou mais. Gini 0,587; os 20% de locais mais avaliados têm 61,2% das avaliações.
- Fala: isso limita qualquer técnica que dependa de histórico em comum.

### 7. Fast food é o mais avaliado e o pior avaliado; as cidades formam ilhas
- Visual: `14_categorias` + `16_mapa_locais`.
- Números: fast food 74.061 avaliações e nota 3,72; Cafe 4,45. Cheyenne, Casper e Jackson à frente; locais em aglomerados isolados.
- Fala: a localização deve pesar na recomendação.

### 8. ◇ O tempo: verão dobra o movimento, e a pandemia corta a série
- Visual: `17_avaliacoes_por_ano` + `18_avaliacoes_por_mes`.
- Números: julho tem 2,05× o movimento de fevereiro (3,29× nas cidades turísticas); avaliações caem de 9.357 (fev/2020) para 906 (abr/2020); a coleta rareia em 2021.
- Fala: por isso a validação cobre um ano inteiro, e o teste começa na pandemia.

## d. Teoria do modelo

### 9. Por que conteúdo e escores de produto
- Tabela das 4 técnicas × cenários 2 e 3 (atende / não atende), com o motivo de cada uma.
- Números das análises: no 5-core, o 20º vizinho de um usuário tem só 4 locais em comum; o local explica 11,5% da variância da nota; 75% das avaliações de uma pessoa ficam na cidade principal dela.
- Fala: é a única técnica que atende sozinha os três cenários usando as notas.

### 10. Conteúdo: o local vira um vetor, e o usuário vira um perfil
- TF-IDF por bloco (categorias + atributos declaráveis), normalização L2, similaridade de cosseno `sim = (cos + 1)/2`.
- Perfil: `p_u ∝ Σ (r_ui − c_u)·x_i`, com `c_u` = média do usuário (cenário 1) ou 3 (cenário 3).
- Visual: `20_vizinhos_conteudo` (os 5 vizinhos de uma pizzaria, um café e um bar são do mesmo tipo).
- Fala: o cosseno mede **tipo** de lugar, não qualidade; por isso os escores.

### 11. Escores de produto: qualidade, popularidade e localização
- Escore bayesiano `(v·R + m·C)/(v + m)`, com `m` no percentil 25 — visual `30_escore_bayesiano` (locais com poucas avaliações puxados para a média).
- Popularidade `log(1+v)/log(1+máx v)`.
- Localização `média de exp(−km/τ)` nos locais avaliados, τ = 200 km — visual `1b_curva_distancia` ◇.

### 12. Uma pontuação, três cenários
- Cenário 1: os quatro componentes, pesos 0,1 / 0,2 / 0,5 / 0,2.
- Cenário 2: o que a pessoa declara (cidade, categorias, atributos, local de exemplo) faz o papel do histórico; pesos 0,05 / 0,19 / 0,475 / 0,285.
- Cenário 3: conteúdo + localização, 0,5 / 0,5, perfil centrado em 3; a lista do usuário antigo reserva 1 posição a um local novo (cota).
- Previsão de nota: escore do local + viés do usuário.

## e. Tratamento dos dados

### 13. Do arquivo bruto à base limpa
- Funil de locais: 12.088 linhas → 72 cópias → 85 sem categoria → 1.863 no recorte de alimentação (8 incluídos à mão, como Bar J Chuckwagon).
- Funil de avaliações: 433.918 → 4.296 duplicatas exatas → 429.622.
- Mantidos com justificativa: texto ausente (41%), rajadas de avaliações (1,4%). Locais fechados (238) continuam na base, mas não são recomendados.

### 14. ◇ O que entra no vetor: só o que um local novo poderia informar
- Entra: categorias e atributos declaráveis (serviço, acessibilidade, comodidades, pagamento, planejamento).
- Fica fora: atributos derivados do comportamento dos clientes, os da pandemia, preço (falta em 90% dos locais sem avaliação e em 5% dos populares) e texto.
- Resultado: 167 tokens (136 de categorias e 31 de atributos).

## f. Treino e teste

### 15. Divisão no tempo: aprender com o passado, medir no futuro
- Visual: `21_divisao_temporal`.
- Tabela: treino até 31/03/2019 (213.626) · validação de um ano (130.071) · teste a partir de 31/03/2020 (85.925, 20%).
- Fala: hiperparâmetros na validação; modelo final reajustado em treino + validação; **o teste foi usado uma única vez**.

### 16. Quem é medido em cada cenário
- Cenário 1: usuários com 3 ou mais avaliações no treino.
- Cenário 2: usuários sem histórico; a 1ª avaliação simula o cadastro (cidade + categoria) e as demais são o alvo.
- Cenário 3: locais novos **naturais** (1ª avaliação depois do corte; 100 no teste) e **simulados** (100 locais antigos com as avaliações escondidas).

## g. Estimação

### 17. Duas perguntas, duas métricas: a pessoa foi? E gostou?
- **Taxa de conversão@10**: fração da lista avaliada com nota 4 ou mais (aonde ela vai).
- **AUC de gosto (curva ROC)**: entre os locais avaliados, os bons acima dos ruins (se gostou).
- Exemplo que justifica as duas: a popularidade converte 7× mais que o acaso, mas empata com ele na AUC de gosto.
- Apoio: MAE/RMSE (nota), correlação de rankings, coberturas, novidade, serendipidade, diversidade.

### 18. Escolha dos pesos: 3,6% de conversão trocados por mais gosto
- Visual: `31_grade_pesos` (fronteira conversão × gosto nas 286 combinações).
- Critério: conversão de pelo menos 95% da melhor e, entre essas, a maior AUC de gosto.
- Escolhido: 0,1 / 0,2 / 0,5 / 0,2, com τ = 200 km, `m` no percentil 25 e perfil centrado na média do usuário. Validação: conversão@10 0,0739 e AUC de gosto 0,5850.

### 19. Ablação: localização e popularidade trazem a pessoa; o escore acerta o gosto
- Visual: `32_ablacao`.
- Números: nenhum componente sozinho passa de 0,0415 de conversão; sem escore, a AUC de gosto cai para 0,4847; sem conteúdo, empata — o conteúdo amplia o catálogo.

### 20. ◇ Cenários 2 e 3 na validação
- Cenário 2: a cidade informada é o que mais ajuda (quase 4× a popularidade global); categorias com peso 0,05 empatam e ampliam o catálogo de 27,9% para 31,8%; como filtro, derrubam a conversão à metade.
- Cenário 3: perfil centrado em 3 (o tipo de lugar que a pessoa frequenta); α = 0,5 somou 0,0119 de AUC de consumo ao só localização; a cota leva o local novo convertido a 149 listas, em vez de 29, mantendo 96% da conversão.

## h. Performance no teste

### 21. Cenário 1: empata com o óbvio na conversão e é o único que acerta o gosto
- Visual: `40_cenario1`.
- Números: modelo 0,0520 de conversão@10 e 0,5542 de AUC de gosto (5.663 usuários). Popularidade + local empata na conversão, mas fica abaixo do acaso no gosto (0,4516). Vizinhos por item, PageRank e o combinado convertem até 25% mais e também ficam abaixo do acaso no gosto.

### 22. Cenário 2: quase 5× a popularidade global para quem nunca avaliou
- Visual: `41_cenario2`.
- Números: 0,0452 de conversão@10 contra 0,0097; AUC de gosto 0,5598 (6.783 usuários); 100% de cobertura de usuários.

### 23. Cenário 3: ordena bem os locais novos, mas o ganho do conteúdo não se confirmou
- Visual: `42_cenario3`.
- Números: AUC de consumo 0,9209 contra 0,9173 só com a localização — **empate** (IC de −0,0008 a 0,0076). Nos simulados, +0,0044, fora do empate. Cota: listas que acertam um local novo passam de 21 para 126, ao custo de 0,0014 de conversão. O conteúdo pontua 100% dos locais novos; vizinhos e PageRank, 0%.

### 24. Curvas ROC, previsão de nota e estabilidade
- Visual: `43_curvas_roc`.
- Previsão de nota: RMSE 1,0248 (escore + viés), contra 1,0842 do escore e 1,1337 da média global.
- Estabilidade: conversão de 0,0504 no 1º ano do teste e 0,0235 depois, em todas as ordenações (pandemia e fim da coleta).

## i. Interface

### 25. Demonstração: o gosto de um usuário e o que o sistema recomenda
- Visual: `50_demonstracao` (gráfico do gosto, notas, mapa e prateleiras no estilo catálogo).
- Fala: **demonstração ao vivo** com `streamlit run app.py`, se houver projetor com a máquina [a decidir].

### 26. Os três cenários na interface
- Visual: `51_usuario_antigo`, `52_usuario_novo` e `53_local_novo` (um slide cada, ou os três juntos ◇).
- Destaques: barras dos componentes e explicação; avisos da regra de não esvaziar; a posição do local novo na lista de um usuário.

## Encerramento

### 27. Conclusões, limitações e próximos passos
- Conclusões: uma técnica atende os três cenários; é a que melhor acerta o gosto entre as que convertem; localização e popularidade trazem a conversão, e o escore, o gosto.
- Limitações: conversão offline é aproximação; pouca personalização (Spearman 0,07); metadados de 2021; teste na pandemia; ganho do conteúdo nos locais novos reais não confirmado.
- Próximos passos: híbrido com vizinhos por item no cenário 1; texto das avaliações no perfil; teste online.

---

## Versão de 15 minutos (proposta)

O tempo é de cerca de 15 minutos. Com uns 2 minutos e meio de demonstração, sobram cerca de 12 para 16 slides, ou 45 segundos cada. Os demais vão para um **apêndice**, para as perguntas.

| Nº | Slide | Junta os do roteiro completo | Tempo |
|---:|---|---|---:|
| 1 | Capa | 1 | 0:15 |
| 2 | O sistema: 3 cenários e como decide | 2 + 3 | 0:50 |
| 3 | A base em números + notas altas | 4 + 5 | 0:50 |
| 4 | Pouco histórico, atenção concentrada | 6 | 0:40 |
| 5 | Categorias e cidades em ilhas | 7 | 0:40 |
| 6 | Por que conteúdo e escores de produto | 9 | 0:50 |
| 7 | Conteúdo: vetor do local e perfil do usuário | 10 | 0:50 |
| 8 | Escores e a pontuação nos 3 cenários | 11 + 12 | 0:55 |
| 9 | Tratamento dos dados | 13 + 14 | 0:40 |
| 10 | Divisão no tempo e quem é medido | 15 + 16 + 8 (pandemia) | 0:50 |
| 11 | Métricas: a pessoa foi? gostou? | 17 | 0:40 |
| 12 | Pesos e ablação | 18 + 19 | 0:55 |
| 13 | Cenário 1 no teste | 21 | 0:45 |
| 14 | Cenários 2 e 3 no teste | 22 + 23 | 0:55 |
| 15 | Interface: demonstração | 25 + 26 | 2:30 |
| 16 | Conclusões e limitações | 27 | 0:45 |
| | **Total** | | **~14:30** |

**Apêndice:** a tabela completa de cada cenário, a sazonalidade (8), os cenários 2 e 3 na validação (20), as curvas ROC, a previsão de nota e a estabilidade (24), e as telas de cada aba (26).

## Decisões

1. **Título:** "Onde comer em Wyoming: recomendação por conteúdo e escores de produto" (provisório, aprovado em 2026-11-05). **Integrantes:** Julia Peixoto e Michele Ughini.
2. **Template:** o modelo simples da usuária no Canva (`modelo_ppt_canva_01.pdf`): fundo bege, títulos em terracota, subtítulos em sálvia, cartões brancos. O PPT gerado serve de base para os slides finais, montados no Canva. Fontes: Century Gothic e Arial no lugar de Montserrat e Inter, que não estão instaladas.
3. **Tempo:** cerca de 15 minutos → versão de 16 slides acima, com apêndice.
4. **Demonstração:** incluída (slide 15, com roteiro ao vivo em 3 passos, e slide 16 e apêndice com as telas de reserva); usar ou não ao vivo ainda será decidido. Recomendação: ao vivo, com o app aberto antes, e vídeo ou telas de reserva.

## Revisão de 2026-11-05: ordem do enunciado e método didático

O `.pptx` gerado passou a ter 24 slides principais, na ordem dos itens do enunciado, com o item no rodapé de cada slide:

1. Capa · 2. Roteiro (os itens b a i) · 3. O sistema (b) · 4–6. Base (c) · 7. Por que conteúdo e escores de produto (d) · 8. O método em uma ideia: quatro perguntas (d) · 9–13. Passos 1 a 5: o local vira vetor, o usuário vira perfil, o cosseno, os escores e a soma num exemplo real (d) · 14. Os três cenários usam a mesma conta (d) · 15. Tratamento: duplicados e ausentes (e) · 16. Treino e teste (f) · 17. O que foi estimado (g) · 18. Escolha dos pesos e ablação (g) · 19. Métricas estudadas em aula (h) · 20–21. Resultados (h) · 22. Demonstração (i) · 23. A interface nos três cenários (i) · 24. Conclusões.

Para caber em 15 minutos, os candidatos a cortar ou juntar são os slides 5 e 6 (base), 7 (escolha da técnica, que pode ir ao apêndice) e 11 (cosseno, que pode se juntar ao 10).

## Revisão de 2026-11-05: slides curtos

A pedido da usuária, um assunto e um visual por slide, com no máximo duas linhas curtas de texto e corpo de 18 pt ou mais; o detalhe vai para as notas do orador. São 41 slides principais (cerca de 20 segundos cada em 15 minutos) e 13 de apêndice:

- **1–2.** Capa · roteiro (seções 1 a 9).
- **3–4. Sistema:** as três situações · como o sistema decide (5 etapas).
- **5–10. Base:** a base em números · as notas são altas · pouco histórico por pessoa · atenção concentrada · categorias · cidades em ilhas.
- **11–23. Teoria:** por que conteúdo e escores de produto · o método em quatro perguntas · a pontuação · passo 1, o local vira uma lista · características raras pesam mais · passo 2, o perfil (notas da Ana) · o perfil da Ana · o perfil de um usuário real · passo 3, o cosseno · passo 4, o escore · passo 4, perto e conhecido · passo 5, a soma decide a ordem · os três cenários usam a mesma conta.
- **24–25. Tratamento:** duplicados e ausentes · o que entra no vetor.
- **26–27. Treino e teste:** divisão no tempo · quem é medido.
- **28–31. Estimação:** o que foi estimado · os pesos de cada cenário · como os pesos foram escolhidos · o papel de cada componente.
- **32–35. Performance:** as métricas · usuário antigo · usuário novo · local novo.
- **36–40. Interface:** roteiro da demonstração · prateleiras · usuário antigo · usuário novo · local novo.
- **41.** Conclusões.
- **Apêndice:** o que os dados mostraram · vizinhos por conteúdo · avaliações por ano e por mês · curvas ROC · previsão de nota · estabilidade · cenários 2 e 3 na validação · telas inteiras.
