"""Estilo único dos gráficos do trabalho."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

COR_PRINCIPAL = "#2a78d6"
COR_SECUNDARIA = "#eb6834"
COR_TEXTO = "#0b0b0b"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_EIXO = "#c3c2b7"
COR_GRADE = "#e1e0d9"
COR_FUNDO = "#fcfcfb"
ESCALA_SEQUENCIAL = LinearSegmentedColormap.from_list("azul", ["#cde2fb", "#3987e5", "#0d366b"])
PASTA_FIGURAS = Path("figuras")


def aplicar_estilo():
    plt.rcParams.update(
        {
            "figure.facecolor": COR_FUNDO,
            "axes.facecolor": COR_FUNDO,
            "savefig.facecolor": COR_FUNDO,
            "font.family": "sans-serif",
            "font.size": 10,
            "text.color": COR_TEXTO,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelcolor": COR_TEXTO_SECUNDARIO,
            "axes.edgecolor": COR_EIXO,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": COR_GRADE,
            "grid.linewidth": 0.8,
            "xtick.color": COR_TEXTO_SECUNDARIO,
            "ytick.color": COR_TEXTO_SECUNDARIO,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "lines.linewidth": 2,
            "figure.dpi": 110,
        }
    )


def numero_br(valor, casas=0):
    """Formata com ponto de milhar e vírgula decimal."""
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def eixo_br(eixo, casas=0):
    """Aplica o formato brasileiro aos números de um eixo do matplotlib."""
    eixo.set_major_formatter(FuncFormatter(lambda valor, _: numero_br(valor, casas)))


def salvar(figura, nome):
    """Grava a figura em `figuras/` e a devolve para aparecer no notebook."""
    PASTA_FIGURAS.mkdir(exist_ok=True)
    figura.savefig(PASTA_FIGURAS / f"{nome}.png", dpi=150, bbox_inches="tight")
    return figura
