# Trabalho T1 de Sistemas de Recomendação

Sistema de recomendação de locais de gastronomia em Wyoming, com a técnica de conteúdo e escores de produto. Trabalho da disciplina Sistemas de Recomendação (PUCRS).

O trabalho está em andamento. O passo a passo e o estado atual estão em [PLANEJAMENTO.md](PLANEJAMENTO.md), e os resultados estão em [relatório.md](relatório.md).

## Dados

A base é a Google Local Data 2021 (McAuley Lab, UCSD), estado de Wyoming. Os dados não ficam neste repositório, porque `review-Wyoming.json` passa do limite de tamanho do GitHub e os dados tratados têm identificadores de usuários e comentários.

Para rodar, coloque `meta-Wyoming.json` e `review-Wyoming.json` na raiz do projeto. Os notebooks geram `data/processed/`.

## Como rodar

Execute os notebooks na ordem, a partir da raiz: `01_dados.ipynb`, `02_preparacao.ipynb`, `03_modelo.ipynb` (grava os modelos em `modelos/`) e `04_avaliacao.ipynb`.

Para abrir a interface, depois do notebook 03:

```bash
streamlit run app.py
```

### Material da apresentação

Tudo o que foi criado para a apresentação está em `scripts/`, com o tema visual em `src/tema_apresentacao.py`:

| Script | O que faz | Saída |
|---|---|---|
| `scripts/graficos_apresentacao.py` | Constrói os gráficos dos slides a partir dos dados e dos modelos, no tema da apresentação | `apresentacao/graficos/` |
| `scripts/capturar_telas.py` | Salva as telas da interface, com o app aberto na porta 8501 | `figuras/50_` a `53_` |
| `scripts/gerar_ppt.py` | Monta os slides com os gráficos e as telas | `apresentacao/T1_Sistema_Recomendacao.pptx` |

Na ordem, depois do notebook 03:

```bash
python scripts/graficos_apresentacao.py
python scripts/capturar_telas.py
python scripts/gerar_ppt.py
```

`graficos_apresentacao.py` aceita as partes que se quer refazer (`base`, `teoria`, `divisao`, `estimacao`, `performance`); a parte `performance` recalcula o teste com os modelos congelados e leva alguns minutos.

Para rodar os testes:

```bash
python -m pytest testes
```
