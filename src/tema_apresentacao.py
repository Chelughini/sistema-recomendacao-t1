"""Tema visual da apresentação, tirado do modelo do grupo no Canva.

Usado por `05_graficos_apresentacao.ipynb` (gráficos) e por `scripts/gerar_ppt.py` (slides), para os
dois falarem a mesma língua visual. Os gráficos do relatório seguem o estilo de `src/graficos.py`.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

CORES = {
    "terracota": "#B44E1C",
    "salvia": "#697967",
    "mostarda": "#CC8B20",
    "texto": "#333F48",
    "suave": "#6B757D",
    "grade": "#E6E1D8",
    "eixo": "#C9C2B6",
    "fundo_slide": "#EDE7DD",
    "cartao": "#F6F2EC",
    "branco": "#FFFFFF",
}
TERRACOTA, SALVIA, MOSTARDA = CORES["terracota"], CORES["salvia"], CORES["mostarda"]

# Do bege claro ao marrom escuro, passando pela terracota: para escalas (nota média, quantidade).
ESCALA = LinearSegmentedColormap.from_list("terracota", ["#F3DDD0", "#D9895E", "#B44E1C", "#5C260C"])

PASTA_GRAFICOS = Path(__file__).resolve().parent.parent / "apresentacao" / "graficos"


def aplicar_tema():
    """Fundo branco, letra grande para ler no projetor, eixos discretos e sem título dentro do gráfico."""
    plt.rcParams.update(
        {
            "figure.facecolor": CORES["branco"],
            "axes.facecolor": CORES["branco"],
            "savefig.facecolor": CORES["branco"],
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "font.size": 14,
            "text.color": CORES["texto"],
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlecolor": CORES["texto"],
            "axes.labelcolor": CORES["suave"],
            "axes.labelsize": 13,
            "axes.edgecolor": CORES["eixo"],
            "axes.linewidth": 1,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": CORES["grade"],
            "grid.linewidth": 1,
            "xtick.color": CORES["suave"],
            "ytick.color": CORES["suave"],
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "lines.linewidth": 3,
            "legend.frameon": False,
            "legend.fontsize": 12,
            "figure.dpi": 100,
        }
    )


def salvar(figura, nome):
    """Grava em `apresentacao/graficos/<nome>.png`, com fundo branco e resolução para projetor."""
    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_GRAFICOS / f"{nome}.png"
    figura.savefig(caminho, dpi=200, bbox_inches="tight", pad_inches=0.15)
    return caminho
