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

Para refazer as telas de `figuras/50_` a `53_`, com o app aberto na porta 8501:

```bash
python scripts/capturar_telas.py
```

Para rodar os testes:

```bash
python -m pytest testes
```
