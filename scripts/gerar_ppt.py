"""Gera a apresentação do Trabalho T1 em `apresentacao/T1_Sistema_Recomendacao.pptx`.

O visual segue o modelo da usuária no Canva (fundo bege, títulos em terracota, cartões brancos).
As fontes do modelo (Montserrat e Inter) não estão instaladas, então os títulos usam Century Gothic
e o texto, Arial; no Canva, volta-se às originais. Os números vêm do `relatório.md`.

Os gráficos vêm de `apresentacao/graficos/`, construídos por `05_graficos_apresentacao.ipynb` no mesmo
tema (`src/tema_apresentacao.py`); as telas da interface vêm de `figuras/50_` a `53_`.

Regra dos slides: um assunto e um visual por slide (uma figura, uma tabela, cartões ou números
grandes), no máximo duas linhas curtas de texto e corpo de 18 pt ou mais; o resto vai para as notas.

    python scripts/gerar_ppt.py
"""

import sys
from pathlib import Path

import numpy as np
from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.tema_apresentacao import CORES as TEMA  # noqa: E402  (as mesmas cores dos gráficos)

FIGURAS = RAIZ / "figuras"
SAIDA = RAIZ / "apresentacao"
RECORTES = SAIDA / "imagens"
GRAFICOS = SAIDA / "graficos"  # gerados por 05_graficos_apresentacao.ipynb
ARQUIVO = SAIDA / "T1_Sistema_Recomendacao.pptx"

# ---------------------------------------------------------------- Tema (do modelo do Canva)
def _cor(nome):
    return RGBColor.from_string(TEMA[nome].lstrip("#"))


FUNDO = _cor("fundo_slide")
BRANCO = _cor("branco")
TERRACOTA = _cor("terracota")
SALVIA = _cor("salvia")
MOSTARDA = _cor("mostarda")
TEXTO = _cor("texto")
SUAVE = _cor("suave")
TINTA_CARTAO = _cor("cartao")
CORES = [TERRACOTA, SALVIA, MOSTARDA, TEXTO]
FONTE_TITULO = "Century Gothic"
FONTE_TEXTO = "Arial"

LARGURA, ALTURA = 13.333, 7.5
MARGEM = 0.39
TOPO_CARTAO = 1.6
BASE_CARTAO = 7.0
CORPO = 18
LEGENDA = 18


# ---------------------------------------------------------------- Peças
def _fundo(slide, cor=FUNDO):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = cor


def _sem_borda(forma):
    forma.line.fill.background()
    forma.shadow.inherit = False


def cartao(slide, x, y, w, h, cor=BRANCO, raio=0.18):
    """Cartão de cantos arredondados; `raio` em polegadas, igual em qualquer tamanho."""
    forma = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    forma.adjustments[0] = min(0.5, raio / min(w, h))
    forma.fill.solid()
    forma.fill.fore_color.rgb = cor
    _sem_borda(forma)
    return forma


def retangulo(slide, x, y, w, h, cor, borda=None):
    forma = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    forma.fill.solid()
    forma.fill.fore_color.rgb = cor
    if borda is None:
        _sem_borda(forma)
    else:
        forma.line.color.rgb = borda
        forma.line.width = Pt(1.5)
        forma.shadow.inherit = False
    return forma


def _marcador(paragrafo, caractere="•", cor=TERRACOTA):
    pPr = paragrafo._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.3)))
    pPr.set("indent", str(-Inches(0.27)))
    for filho in list(pPr):
        if filho.tag in (qn("a:buNone"), qn("a:buChar"), qn("a:buClr")):
            pPr.remove(filho)
    clr = etree.SubElement(pPr, qn("a:buClr"))
    srgb = etree.SubElement(clr, qn("a:srgbClr"))
    srgb.set("val", str(cor))
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", caractere)


def texto(slide, x, y, w, h, linhas, tamanho=CORPO, cor=TEXTO, fonte=FONTE_TEXTO, negrito=False, alinhar=PP_ALIGN.LEFT,
          ancora=MSO_ANCHOR.TOP, espaco=6, marcadores=False):
    """Caixa de texto. `linhas` é um texto ou uma lista; cada item é um texto ou uma lista de trechos
    (texto, {opções}) com as chaves negrito, cor, tamanho, fonte e italico."""
    caixa = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    quadro = caixa.text_frame
    quadro.word_wrap = True
    quadro.vertical_anchor = ancora
    for lado in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(quadro, lado, 0)
    if isinstance(linhas, str):
        linhas = [linhas]
    for i, linha in enumerate(linhas):
        p = quadro.paragraphs[0] if i == 0 else quadro.add_paragraph()
        p.alignment = alinhar
        p.space_after = Pt(espaco)
        trechos = linha if isinstance(linha, list) else [(linha, {})]
        for conteudo, opcoes in trechos:
            r = p.add_run()
            r.text = conteudo
            f = r.font
            f.name = opcoes.get("fonte", fonte)
            f.size = Pt(opcoes.get("tamanho", tamanho))
            f.bold = opcoes.get("negrito", negrito)
            f.italic = opcoes.get("italico", False)
            f.color.rgb = opcoes.get("cor", cor)
        if marcadores:
            _marcador(p)
    return caixa


def imagem(slide, caminho, x, y, w, h, topo=False):
    """Imagem centrada na área (ou no topo dela), sem distorcer; devolve a base da imagem, em polegadas."""
    largura, altura = Image.open(caminho).size
    escala = min(w / largura, h / altura)
    lw, lh = largura * escala, altura * escala
    y0 = y if topo else y + (h - lh) / 2
    slide.shapes.add_picture(str(caminho), Inches(x + (w - lw) / 2), Inches(y0), Inches(lw), Inches(lh))
    return y0 + lh


def notas(slide, fala):
    slide.notes_slide.notes_text_frame.text = fala


def circulo(slide, x, y, marca, cor, d=0.6):
    forma = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    forma.fill.solid()
    forma.fill.fore_color.rgb = cor
    _sem_borda(forma)
    quadro = forma.text_frame
    quadro.margin_left = quadro.margin_right = quadro.margin_top = quadro.margin_bottom = 0
    quadro.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = quadro.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(marca)
    r.font.name = FONTE_TITULO
    r.font.bold = True
    r.font.size = Pt(18 * d / 0.5)
    r.font.color.rgb = BRANCO


def seta(slide, x1, y1, x2, y2, cor=SALVIA):
    linha = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    linha.line.color.rgb = cor
    linha.line.width = Pt(2.5)
    ln = linha.line._get_or_add_ln()
    cauda = etree.SubElement(ln, qn("a:tailEnd"))
    cauda.set("type", "triangle")
    return linha


def tabela(slide, linhas, x, y, w, h, larguras, tamanho=CORPO, centro=True, destacar=None):
    """Tabela no estilo do modelo: cabeçalho em terracota e linhas alternadas; `destacar` é o índice de uma linha em negrito."""
    t = slide.shapes.add_table(len(linhas), len(linhas[0]), Inches(x), Inches(y), Inches(w), Inches(h)).table
    for j, fracao in enumerate(larguras):
        t.columns[j].width = Inches(w * fracao)
    for i, linha in enumerate(linhas):
        for j, valor in enumerate(linha):
            celula = t.cell(i, j)
            celula.fill.solid()
            celula.fill.fore_color.rgb = TERRACOTA if i == 0 else (TINTA_CARTAO if i % 2 == 0 else BRANCO)
            celula.text_frame.text = valor
            celula.margin_left = celula.margin_right = Inches(0.1)
            celula.vertical_anchor = MSO_ANCHOR.MIDDLE
            paragrafo = celula.text_frame.paragraphs[0]
            paragrafo.alignment = PP_ALIGN.CENTER if (centro and j > 0) else PP_ALIGN.LEFT
            if not paragrafo.runs:
                continue
            fonte = paragrafo.runs[0].font
            fonte.name, fonte.size = FONTE_TEXTO, Pt(tamanho)
            fonte.bold = i == 0 or j == 0 or i == destacar
            fonte.color.rgb = BRANCO if i == 0 else TEXTO
    return t


def br(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def sinal(valor, casas=2):
    return f"{valor:+.{casas}f}".replace(".", ",")


def tracos(slide, x, y):
    for i, cor in enumerate([TERRACOTA, SALVIA, MOSTARDA]):
        retangulo(slide, x + i * 0.67, y, 0.53, 0.09, cor)


def circulo_branco(slide):
    forma = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.0), Inches(-0.82), Inches(8.87), Inches(8.87))
    forma.fill.solid()
    forma.fill.fore_color.rgb = BRANCO
    _sem_borda(forma)


# ---------------------------------------------------------------- Seções e modelos de slide
SECOES = {
    "sistema": "1 · Descrição do sistema",
    "base": "2 · Base de dados",
    "teoria": "3 · Conceitos teóricos do modelo",
    "tratamento": "4 · Tratamento dos dados",
    "divisao": "5 · Treino e teste",
    "estimacao": "6 · Estimação do modelo",
    "performance": "7 · Performance do modelo",
    "interface": "8 · Interface nos 3 cenários",
    "conclusoes": "9 · Conclusões",
    "apendice": "Apêndice",
}
_SECAO = {"atual": None}


def secao(chave):
    """Define a seção dos próximos slides; ela aparece no rodapé."""
    _SECAO["atual"] = SECOES.get(chave) if chave else None


def novo_slide(p, titulo, mensagem=None):
    """Layout de conteúdo: título em terracota, a mensagem em sálvia e a seção no rodapé."""
    slide = p.slides.add_slide(p.slide_layouts[6])
    _fundo(slide)
    if _SECAO["atual"]:
        texto(slide, LARGURA - MARGEM - 5.0, 7.13, 5.0, 0.28, _SECAO["atual"], tamanho=12, cor=SUAVE, alinhar=PP_ALIGN.RIGHT, espaco=0)
    texto(slide, MARGEM, 0.28, LARGURA - 2 * MARGEM, 0.75, titulo, tamanho=36, cor=TERRACOTA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    if mensagem:
        texto(slide, MARGEM, 0.98, LARGURA - 2 * MARGEM, 0.5, mensagem, tamanho=20, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    return slide


def slide_figura(p, titulo, mensagem, caminho, legenda, fala):
    """Uma figura grande num cartão e, se houver, uma linha de legenda abaixo dela."""
    s = novo_slide(p, titulo, mensagem)
    cartao(s, MARGEM, TOPO_CARTAO, LARGURA - 2 * MARGEM, BASE_CARTAO - TOPO_CARTAO)
    espaco_legenda = 0.75 if legenda else 0
    base = imagem(s, caminho, MARGEM + 0.35, TOPO_CARTAO + 0.25, LARGURA - 2 * MARGEM - 0.7, BASE_CARTAO - TOPO_CARTAO - 0.45 - espaco_legenda)
    if legenda:
        texto(s, MARGEM + 0.5, base + 0.15, LARGURA - 2 * MARGEM - 1.0, 0.6, legenda, tamanho=LEGENDA, alinhar=PP_ALIGN.CENTER, espaco=0)
    notas(s, fala)
    return s


def slide_numeros(p, titulo, mensagem, numeros, fala, colunas=3):
    """Números grandes, cada um num cartão, com o rótulo embaixo."""
    s = novo_slide(p, titulo, mensagem)
    linhas = int(np.ceil(len(numeros) / colunas))
    vao = 0.3
    largura = (LARGURA - 2 * MARGEM - vao * (colunas - 1)) / colunas
    altura = (BASE_CARTAO - TOPO_CARTAO - vao * (linhas - 1)) / linhas
    topo = TOPO_CARTAO
    if linhas == 1:
        altura = 3.2
        topo = TOPO_CARTAO + (BASE_CARTAO - TOPO_CARTAO - altura) / 2
    tamanho = 48 if linhas == 1 else 40
    for k, (valor, rotulo, cor) in enumerate(numeros):
        x = MARGEM + (k % colunas) * (largura + vao)
        y = topo + (k // colunas) * (altura + vao)
        cartao(s, x, y, largura, altura)
        texto(s, x + 0.35, y + altura * 0.18, largura - 0.7, 0.9, valor, tamanho=tamanho, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.35, y + altura * 0.18 + (1.05 if tamanho == 48 else 0.9), largura - 0.7, altura * 0.55, rotulo, tamanho=CORPO, cor=TEXTO, espaco=0)
    notas(s, fala)
    return s


def slide_cartoes(p, titulo, mensagem, itens, fala, altura=None):
    """Um cartão por item, lado a lado: marca colorida, título e uma ou duas linhas."""
    s = novo_slide(p, titulo, mensagem)
    n = len(itens)
    vao = 0.3
    largura = (LARGURA - 2 * MARGEM - vao * (n - 1)) / n
    altura = altura or (4.4 if n >= 4 else 3.8)
    topo = TOPO_CARTAO + (BASE_CARTAO - TOPO_CARTAO - altura) / 2
    for k, (marca, cor, nome, descricao) in enumerate(itens):
        x = MARGEM + k * (largura + vao)
        cartao(s, x, topo, largura, altura)
        circulo(s, x + 0.35, topo + 0.4, marca, cor, d=0.7)
        texto(s, x + 0.35, topo + 1.35, largura - 0.7, 1.4, nome, tamanho=22, negrito=True, fonte=FONTE_TITULO, espaco=0)
        y_texto = topo + (2.85 if n >= 4 else 2.25)
        texto(s, x + 0.35, y_texto, largura - 0.7, topo + altura - y_texto - 0.2, descricao, tamanho=CORPO, espaco=8)
    notas(s, fala)
    return s


def slide_tabela(p, titulo, mensagem, linhas, larguras, fala, legenda=None, tamanho=CORPO, destacar=None):
    s = novo_slide(p, titulo, mensagem)
    altura = min(0.62 * len(linhas), BASE_CARTAO - TOPO_CARTAO - (1.5 if legenda else 0.8))
    altura_cartao = 0.45 + altura + (1.15 if legenda else 0.45)
    topo = TOPO_CARTAO + (BASE_CARTAO - TOPO_CARTAO - altura_cartao) / 2
    cartao(s, MARGEM, topo, LARGURA - 2 * MARGEM, altura_cartao)
    tabela(s, linhas, MARGEM + 0.45, topo + 0.45, LARGURA - 2 * MARGEM - 0.9, altura, larguras, tamanho=tamanho, destacar=destacar)
    if legenda:
        texto(s, MARGEM + 0.45, topo + 0.45 + altura + 0.4, LARGURA - 2 * MARGEM - 0.9, 0.5, legenda, tamanho=LEGENDA, espaco=0)
    notas(s, fala)
    return s


# ---------------------------------------------------------------- Recortes das telas
def preparar_recortes():
    RECORTES.mkdir(parents=True, exist_ok=True)
    demo = Image.open(FIGURAS / "50_demonstracao.png")
    antigo = Image.open(FIGURAS / "51_usuario_antigo.png")
    novo = Image.open(FIGURAS / "52_usuario_novo.png")
    local = Image.open(FIGURAS / "53_local_novo.png")
    recortes = {
        "demo_prateleira.png": (demo, (360, 1180, 1740, 1520)),
        "tela_antigo.png": (antigo, (370, 640, 1730, 1090)),
        "tela_novo.png": (novo, (370, 715, 1730, 1205)),
        "tela_local.png": (local, (370, 410, 1730, 1150)),
        "inteira_antigo.png": (antigo, (360, 90, 1740, 1130)),
        "inteira_novo.png": (novo, (360, 90, 1740, 1210)),
        "inteira_local.png": (local, (360, 90, 1740, 1160)),
    }
    for nome, (origem, caixa) in recortes.items():
        origem.crop(caixa).save(RECORTES / nome)


# ---------------------------------------------------------------- Exemplo de brinquedo (Ana)
CARACTERISTICAS = ["Pizzaria", "Café", "Bar", "Entrega", "Mesas ao ar livre"]
AVALIADOS = [("Pizzaria A", [1, 0, 0, 1, 0], 5), ("Café B", [0, 1, 0, 1, 0], 2), ("Bar C", [0, 0, 1, 0, 1], 4)]
CANDIDATOS = [("Pizzaria D", [1, 0, 0, 1, 0]), ("Café E", [0, 1, 0, 0, 1])]


def exemplo_ana():
    """Contas do exemplo, feitas aqui (sem o TF-IDF, para os números do slide fecharem)."""
    media = np.mean([nota for _, _, nota in AVALIADOS])
    pesos = [nota - media for _, _, nota in AVALIADOS]
    perfil = sum(peso * np.array(vetor, float) for peso, (_, vetor, _) in zip(pesos, AVALIADOS))
    similaridades = []
    for nome, vetor in CANDIDATOS:
        v = np.array(vetor, float)
        cosseno = perfil @ v / (np.linalg.norm(perfil) * np.linalg.norm(v))
        similaridades.append((nome, (cosseno + 1) / 2))
    return media, pesos, perfil, similaridades


# ---------------------------------------------------------------- Abertura
def capa(p):
    s = p.slides.add_slide(p.slide_layouts[6])
    _fundo(s)
    circulo_branco(s)
    imagem(s, GRAFICOS / "base_mapa.png", 7.75, 1.2, 5.2, 5.0)
    texto(s, 0.75, 0.68, 6.5, 0.4, "PUCRS · Sistemas de Recomendação · Prof. Rafael Scopel, PhD", tamanho=14, cor=TERRACOTA, espaco=0)
    texto(s, 0.75, 1.55, 6.3, 2.6, ["Onde comer", "em Wyoming"], tamanho=58, cor=TERRACOTA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(s, 0.75, 4.05, 6.0, 0.9, "Recomendação por conteúdo e escores de produto", tamanho=20, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(s, 0.75, 5.3, 6.0, 0.9, ["Julia Peixoto e Michele Ughini", "Novembro de 2026"], tamanho=16, cor=TEXTO, espaco=4)
    tracos(s, 0.75, 6.69)
    notas(s, "Apresentar o grupo e o tema: um sistema que recomenda restaurantes, cafés e bares de Wyoming a partir das avaliações do Google, com a técnica de conteúdo e escores de produto.")


def roteiro(p):
    secao(None)
    s = novo_slide(p, "Roteiro")
    nomes = ["Descrição do sistema", "Base de dados", "Conceitos teóricos do modelo", "Tratamento dos dados", "Treino e teste",
             "Estimação do modelo", "Performance do modelo", "Interface nos 3 cenários", "Conclusões"]
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    altura = (BASE_CARTAO - TOPO_CARTAO - 0.6) / 3
    for k, nome in enumerate(nomes):
        x = MARGEM + (k % 3) * (largura + 0.3)
        y = TOPO_CARTAO + (k // 3) * (altura + 0.3)
        cartao(s, x, y, largura, altura)
        circulo(s, x + 0.3, y + (altura - 0.6) / 2, k + 1, CORES[k % 3])
        texto(s, x + 1.1, y, largura - 1.3, altura, nome, tamanho=CORPO, negrito=True, fonte=FONTE_TITULO, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
    notas(s, "A apresentação segue a ordem dos itens do enunciado (as seções 1 a 8 são os itens b a i; o item a é a capa). O rodapé de cada slide indica a seção.")


# ---------------------------------------------------------------- 1. Sistema
def sistema(p):
    secao("sistema")
    slide_cartoes(p, "O sistema", "Recomendar onde comer a quem avalia no Google, em três situações", [
        (1, TERRACOTA, "Usuário antigo", "Uma lista de locais a partir do histórico de notas"),
        (2, SALVIA, "Usuário novo", "Uma lista a partir do que a pessoa informa"),
        (3, MOSTARDA, "Local novo", "Para quais usuários indicar um local recém-aberto"),
    ], "O enunciado pede três cenários, e eles são frequentes na base: 66% dos usuários têm uma única avaliação, e de 51% a 57% das avaliações vêm de usuários novos.")

    s = novo_slide(p, "Como o sistema decide", "Dos dados à lista com explicação, em cinco etapas")
    etapas = ["Avaliações e dados dos locais", "Características e escores de cada local", "Perfil do usuário", "Pontuação de cada local", "Lista com explicação"]
    largura, vao = 2.15, 0.42
    x0 = (LARGURA - (5 * largura + 4 * vao)) / 2
    y = TOPO_CARTAO + 1.3
    for k, etapa in enumerate(etapas):
        x = x0 + k * (largura + vao)
        cartao(s, x, y, largura, 2.4)
        circulo(s, x + (largura - 0.6) / 2, y + 0.3, k + 1, CORES[k % 3])
        texto(s, x + 0.15, y + 1.1, largura - 0.3, 1.2, etapa, tamanho=16, negrito=True, alinhar=PP_ALIGN.CENTER, espaco=0)
        if k < 4:
            seta(s, x + largura + 0.06, y + 1.2, x + largura + vao - 0.06, y + 1.2)
    notas(s, "O sistema descreve cada local por suas características e escores, monta um perfil de cada usuário, pontua os locais e devolve os 10 primeiros, cada um com o porquê ('porque você gostou de X').")


# ---------------------------------------------------------------- 2. Base
def base(p):
    secao("base")
    slide_numeros(p, "A base", "Google Local 2021: restaurantes, cafés e bares de Wyoming", [
        ("429.622", "avaliações, cada uma com usuário e nota", TERRACOTA),
        ("175.278", "usuários", TERRACOTA),
        ("1.863", "locais", TEXTO),
        ("115", "cidades", TEXTO),
        ("2008–2021", "período das avaliações", TEXTO),
        ("99,87%", "da matriz usuário × local está vazia", SALVIA),
    ], "A base atende a exigência do enunciado: cada avaliação tem usuário e nota. Fonte: McAuley Lab (UCSD), recorte do estado de Wyoming pela categoria principal de alimentação. A matriz quase vazia limita qualquer técnica que dependa de histórico em comum.")
    slide_figura(p, "As notas são altas", "78% das avaliações são 4 ou 5", GRAFICOS / "base_notas.png",
                 "Por isso, \"relevante\" no trabalho é nota 4 ou mais", "A nota 5 sozinha tem 55,6% das avaliações. Notas de 1 a 3 são o sinal mais raro.")
    slide_figura(p, "Pouco histórico por pessoa", "66% dos usuários avaliaram um único local", GRAFICOS / "base_atividade.png",
                 "Só 10,4% têm 5 ou mais avaliações", "A maioria das pessoas tem pouquíssimo histórico, o que torna importante o cenário de usuário novo e limita as técnicas colaborativas.")
    slide_figura(p, "Atenção concentrada", "20% dos locais recebem 61% das avaliações", GRAFICOS / "base_concentracao.png",
                 "O mais avaliado é o Texas Roadhouse de Cheyenne, com 2.598", "Índice de Gini de 0,587: a atenção é concentrada, mas sem domínio extremo. A mediana é de 123 avaliações por local.")
    slide_figura(p, "Categorias", "Fast food é a categoria mais avaliada e a de menor nota", GRAFICOS / "base_categorias.png",
                 "Fast food: 74.061 avaliações e nota 3,72 · Cafe: a maior nota, 4,45", "A nota varia por categoria, o que abre espaço para usar a qualidade do local como sinal.")
    slide_figura(p, "Cidades em ilhas", "As pessoas avaliam sobretudo na própria cidade", GRAFICOS / "base_mapa.png",
                 "75% das avaliações de uma pessoa ficam na cidade principal dela", "Os locais formam aglomerados isolados, com grandes vazios entre as cidades: a localização deve pesar na recomendação.")
    slide_figura(p, "Avaliações por mês", "Julho tem 2 vezes o movimento de fevereiro", GRAFICOS / "base_por_mes.png", None,
                 "De 2017 a 2019; 3,29 vezes nas cidades turísticas. Por isso a validação cobre um ano inteiro.")


# ---------------------------------------------------------------- 3. Teoria
def teoria(p):
    secao("teoria")
    slide_tabela(p, "Por que conteúdo e escores de produto", "É a única das quatro técnicas que atende os três cenários usando as notas", [
        ["Técnica", "Usuário novo", "Local novo"],
        ["Conteúdo e escores de produto", "Atende", "Atende"],
        ["Vizinhos próximos", "Não atende", "Não atende"],
        ["Bases de conhecimento", "Atende", "Sem usar as notas"],
        ["Redes e grafos", "Não atende", "Não atende"],
    ], [0.46, 0.27, 0.27], "Vizinhos e grafos precisam de avaliações em comum, que o usuário novo e o local novo não têm. Bases de conhecimento não usariam as notas dos usuários. "
       "Os dados apoiam os componentes: no 5-core, o 20º vizinho de um usuário tem só 4 locais em comum; o local explica 11,5% da variância da nota; e 75% das avaliações de uma pessoa ficam na cidade principal dela.", destacar=1)

    slide_cartoes(p, "O método em uma ideia", "Para cada local, o sistema faz quatro perguntas", [
        (1, TERRACOTA, "É parecido com o que você gostou?", "Conteúdo"),
        (2, SALVIA, "É bom?", "Escore"),
        (3, MOSTARDA, "É perto de onde você anda?", "Localização"),
        (4, TEXTO, "Muita gente vai?", "Popularidade"),
    ], "A primeira pergunta é o conteúdo: o local se parece com os que a pessoa gostou? As outras três são os escores de produto, que descrevem o local em si. Nos próximos slides, cada uma com um exemplo.")

    s = novo_slide(p, "A pontuação", "Cada resposta vira um número de 0 a 1, e a pontuação soma as quatro com pesos")
    cartao(s, MARGEM, TOPO_CARTAO, LARGURA - 2 * MARGEM, BASE_CARTAO - TOPO_CARTAO)
    texto(s, MARGEM + 0.3, TOPO_CARTAO + 1.3, LARGURA - 2 * MARGEM - 0.6, 0.8,
          "pontuação = α × conteúdo + β × escore + γ × localização + δ × popularidade", tamanho=26, cor=TERRACOTA, negrito=True, alinhar=PP_ALIGN.CENTER, espaco=0)
    texto(s, MARGEM + 0.5, TOPO_CARTAO + 2.9, LARGURA - 2 * MARGEM - 1.0, 1.5, [
        "A lista são os 10 locais com maior pontuação,",
        "entre os abertos que a pessoa ainda não avaliou.",
    ], tamanho=22, alinhar=PP_ALIGN.CENTER, espaco=4)
    notas(s, "Os pesos α, β, γ e δ são escolhidos na validação (seção 6).")

    linhas = [["Local"] + CARACTERISTICAS] + [[nome] + ["✓" if marca else "" for marca in vetor] for nome, vetor, _ in AVALIADOS]
    slide_tabela(p, "Passo 1: o local vira uma lista", "Cada local é descrito pelas características que ele mesmo informa", linhas, [0.2] + [0.16] * 5,
                 "Na base real são 167 características: 136 categorias (pizzaria, café, churrascaria…) e 31 atributos (entrega, acessibilidade, formas de pagamento…). Só entra o que um local recém-aberto poderia informar.",
                 legenda="Na base real: 167 características, entre categorias e atributos")

    slide_numeros(p, "Características raras pesam mais", "O TF-IDF dá mais peso ao que distingue um local", [
        ("1,08", "peso de \"Entrega\": quase todo local tem", SUAVE),
        ("7,31", "peso de \"Loja de pretzel\": pouquíssimos têm", TERRACOTA),
    ], "O TF-IDF multiplica cada característica pelo quanto ela é rara na base. Depois, cada vetor é normalizado para ter tamanho 1, e a comparação fica justa entre locais com muitas e poucas características.", colunas=2)

    media, pesos, perfil, similaridades = exemplo_ana()
    slide_tabela(p, "Passo 2: o usuário vira um perfil", f"A Ana avaliou três locais; a média dela é {br(media)}",
                 [["Local", "Nota", "Nota − média"]] + [[nome, str(nota), sinal(peso)] for (nome, _, nota), peso in zip(AVALIADOS, pesos)],
                 [0.4, 0.25, 0.35], "Cada local entra no perfil com o peso da nota menos a média da pessoa: o que ela avaliou acima da própria média soma; o que avaliou abaixo, subtrai.",
                 legenda="Acima da média soma ao perfil; abaixo, subtrai")

    s = novo_slide(p, "O perfil da Ana", "Ela gosta de pizzaria e não gosta de café")
    cartao(s, MARGEM, TOPO_CARTAO, LARGURA - 2 * MARGEM, BASE_CARTAO - TOPO_CARTAO)
    maior = max(abs(v) for v in perfil)
    meio = LARGURA / 2 + 0.6
    meia = 3.6
    topo = TOPO_CARTAO + 0.55
    for k, (nome, valor) in enumerate(zip(CARACTERISTICAS, perfil)):
        y = topo + k * 0.92
        texto(s, MARGEM + 0.6, y, 3.4, 0.6, nome, tamanho=CORPO, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        comprimento = abs(valor) / maior * meia
        if comprimento > 0.01:
            retangulo(s, meio if valor > 0 else meio - comprimento, y + 0.1, comprimento, 0.42, TERRACOTA if valor > 0 else SALVIA)
        x = meio + comprimento + 0.12 if valor > 0 else meio - comprimento - 1.0
        texto(s, x, y, 0.9, 0.6, sinal(valor), tamanho=CORPO, negrito=True, ancora=MSO_ANCHOR.MIDDLE, alinhar=PP_ALIGN.LEFT if valor > 0 else PP_ALIGN.RIGHT, espaco=0)
    linha = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(meio), Inches(topo - 0.1), Inches(meio), Inches(topo + 5 * 0.92 - 0.2))
    linha.line.color.rgb = SUAVE
    linha.line.width = Pt(1.25)
    notas(s, "O perfil é a soma das características com esses pesos: pizzaria +1,33, café −1,67. 'Entrega' fica levemente negativa porque aparece na pizzaria (gostou) e no café (não gostou).")

    slide_figura(p, "O perfil de um usuário real", "Usuário #12.369, de Riverton", GRAFICOS / "teoria_perfil_usuario.png",
                 None, "O mesmo cálculo, num usuário real da base, como aparece na interface: restaurante americano e mesas ao ar livre de um lado; restaurante genérico e drive-thru do outro.")

    s = novo_slide(p, "Passo 3: \"parecido\" é o cosseno", "Compara o perfil com cada local: perto de 1 é parecido; perto de 0, o oposto")
    largura = (LARGURA - 2 * MARGEM - 0.3) / 2
    for k, ((nome, vetor), (_, similaridade)) in enumerate(zip(CANDIDATOS, similaridades)):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO - 1.0)
        texto(s, x + 0.45, TOPO_CARTAO + 0.4, largura - 0.9, 0.6, nome, tamanho=26, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 1.1, largura - 0.9, 0.6, ", ".join(c for c, marca in zip(CARACTERISTICAS, vetor) if marca), tamanho=CORPO, cor=SUAVE, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 2.0, largura - 0.9, 1.4, br(similaridade), tamanho=72, cor=TERRACOTA if similaridade > 0.5 else SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(s, MARGEM, BASE_CARTAO - 0.7, LARGURA - 2 * MARGEM, 0.6, "conteúdo = (cosseno + 1) / 2", tamanho=22, cor=TERRACOTA, negrito=True, alinhar=PP_ALIGN.CENTER, espaco=0)
    notas(s, "O cosseno mede o ângulo entre o perfil e o vetor do local: o mesmo lado dá 1; lados opostos dão −1; a conta leva para 0 a 1. A Pizzaria D, parecida com o que a Ana gostou, fica com "
             f"{br(similaridades[0][1])}; o Café E, com {br(similaridades[1][1])}. Atenção: o cosseno mede o tipo de lugar, não a qualidade — por isso entram os escores.")

    s = novo_slide(p, "Passo 4: o escore do local", "Uma média que desconfia de quem tem poucas avaliações")
    largura = (LARGURA - 2 * MARGEM - 0.3) / 2
    casos = [("2 avaliações", "média 5,0", "4,18", SALVIA), ("400 avaliações", "média 4,7", "4,65", TERRACOTA)]
    for k, (avaliacoes, media_local, escore, cor) in enumerate(casos):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO - 1.0)
        texto(s, x + 0.45, TOPO_CARTAO + 0.4, largura - 0.9, 0.6, avaliacoes, tamanho=26, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 1.1, largura - 0.9, 0.6, media_local, tamanho=CORPO, cor=SUAVE, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 2.0, largura - 0.9, 1.4, escore, tamanho=72, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(s, MARGEM, BASE_CARTAO - 0.7, LARGURA - 2 * MARGEM, 0.6, "Com poucas avaliações, o escore fica perto da média geral (4,13)", tamanho=22, cor=TERRACOTA, negrito=True, alinhar=PP_ALIGN.CENTER, espaco=0)
    notas(s, "É a média bayesiana: escore = (v · média do local + m · 4,13) / (v + m), com m = 36,8 avaliações. Sem isso, um local com duas notas 5 passaria à frente de um com 400 avaliações e média 4,7.")

    slide_figura(p, "Escore bayesiano na base", "Com poucas avaliações, o escore fica perto da média geral", GRAFICOS / "teoria_escore.png", None,
                 "Cada ponto é um local: a média simples das notas contra o escore. Os locais com poucas avaliações (cores claras) ficam perto da média geral, 4,13; os com muitas, perto da diagonal.")

    slide_tabela(p, "Passo 4: perto e conhecido", "A localização cai com a distância; a popularidade cresce devagar", [
        ["Distância até onde a pessoa avalia", "Localização", "Avaliações do local", "Popularidade"],
        ["0 km", "1,00", "10", "0,31"],
        ["50 km", "0,78", "100", "0,59"],
        ["200 km", "0,37", "500", "0,79"],
        ["500 km", "0,08", "2.598 (o máximo)", "1,00"],
    ], [0.32, 0.18, 0.3, 0.2], "Localização: média de exp(−km / 200) até os locais que a pessoa já avaliou. Popularidade: log(1 + avaliações) / log(1 + máximo); o logaritmo evita que os gigantes dominem.")

    s = novo_slide(p, "Passo 5: a soma decide a ordem", "Usuário #12.369, de Riverton: o melhor escore da base fica em 375º por estar longe")
    cartao(s, MARGEM, TOPO_CARTAO, LARGURA - 2 * MARGEM, BASE_CARTAO - TOPO_CARTAO)
    componentes = [("Conteúdo", 0.1, TERRACOTA), ("Escore", 0.2, SALVIA), ("Localização", 0.5, MOSTARDA), ("Popularidade", 0.2, SUAVE)]
    locais = [("The Depot Restaurant", "Riverton", "1º", [0.551, 0.840, 0.691, 0.777]),
              ("Bar J Chuckwagon Suppers", "Wilson", "375º", [0.476, 0.941, 0.260, 0.880])]
    escala = 5.6 / 0.75
    for k, (nome, cidade, posicao, valores) in enumerate(locais):
        y = TOPO_CARTAO + 0.6 + k * 1.75
        texto(s, MARGEM + 0.45, y - 0.05, 4.0, 0.45, nome, tamanho=CORPO, negrito=True, espaco=0)
        texto(s, MARGEM + 0.45, y + 0.45, 4.0, 0.4, cidade, tamanho=16, cor=SUAVE, espaco=0)
        inicio = MARGEM + 4.6
        for (_, peso, cor), valor in zip(componentes, valores):
            largura = peso * valor * escala
            retangulo(s, inicio, y, largura, 0.8, cor, borda=BRANCO)
            inicio += largura
        total = sum(peso * v for (_, peso, _), v in zip(componentes, valores))
        texto(s, inicio + 0.2, y, 2.0, 0.8, [[(br(total, 3), {"negrito": True}), (f"  {posicao}", {"negrito": True, "cor": TERRACOTA})]], tamanho=22, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
    inicio = MARGEM + 0.45
    for nome, peso, cor in componentes:
        retangulo(s, inicio, BASE_CARTAO - 0.85, 0.28, 0.28, cor)
        texto(s, inicio + 0.38, BASE_CARTAO - 0.92, 2.4, 0.42, f"{nome} ({br(peso, 1)})", tamanho=16, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        inicio += 2.9
    notas(s, "Cada barra é a soma dos quatro componentes, cada um multiplicado pelo seu peso. O The Depot Restaurant tem escore bom, é perto e é popular: 0,724, em 1º. "
             "O Bar J Chuckwagon Suppers tem o melhor escore da base (0,94), mas fica em Wilson, longe: a localização cai para 0,26, e ele vai a 375º de 1.508. A localização, com peso 0,5, é o que mais move a ordem.")

    slide_cartoes(p, "Os três cenários usam a mesma conta", "Muda de onde vem o perfil e quais perguntas têm resposta", [
        (1, TERRACOTA, "Usuário antigo", "Perfil vindo do histórico; as quatro perguntas"),
        (2, SALVIA, "Usuário novo", "Perfil vindo do que a pessoa informa: cidade, gostos, um local"),
        (3, MOSTARDA, "Local novo", "Sem avaliações: só conteúdo e localização"),
    ], "Para o usuário novo, a localização é a distância ao centro da cidade informada, e tudo é opcional. Para o local novo, não há escore nem popularidade: é o conteúdo que permite recomendá-lo. "
       "A lista do usuário antigo ainda reserva 1 posição a um local novo. A nota prevista, mostrada na interface, é o escore do local mais o viés do usuário.")


# ---------------------------------------------------------------- 4. Tratamento
def tratamento(p):
    secao("tratamento")
    slide_tabela(p, "Duplicados e ausentes", "O que havia e o que foi feito com cada um", [
        ["Problema", "Quanto", "Tratamento"],
        ["Local repetido", "72", "Removido"],
        ["Avaliação duplicada", "4.296", "Removida"],
        ["Local sem categoria", "85", "Removido"],
        ["Nota ou usuário ausente", "0", "—"],
        ["Avaliação sem texto", "41,3%", "Mantida (o texto não entra)"],
        ["Local sem preço", "37,1%", "Fora do vetor; filtro na interface"],
        ["Local fechado", "238", "Fica na base, não é recomendado"],
    ], [0.36, 0.16, 0.48], "Duplicados: 72 cópias idênticas de locais e 4.296 avaliações repetidas, removidas; não havia avaliação repetida do mesmo usuário no mesmo local. "
       "Ausentes: nenhuma nota ou usuário faltando; 85 locais sem categoria saíram; 7 locais sem cidade usam a coordenada. O recorte de alimentação deixou 1.863 dos 12.016 locais e 429.622 avaliações.", tamanho=17)

    s = novo_slide(p, "O que entra no vetor", "Só o que um local recém-aberto poderia informar")
    largura = (LARGURA - 2 * MARGEM - 0.3) / 2
    colunas = [("Entra", SALVIA, ["Categorias", "Serviço (entrega, para viagem…)", "Acessibilidade", "Comodidades e pagamento"]),
               ("Fica fora", TERRACOTA, ["Atributos que vêm dos clientes (\"popular para\", público)", "Atributos da pandemia", "Preço (falta nos locais pouco avaliados)", "Texto das avaliações"])]
    for k, (nome, cor, itens) in enumerate(colunas):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO)
        texto(s, x + 0.45, TOPO_CARTAO + 0.35, largura - 0.9, 0.6, nome, tamanho=26, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 1.25, largura - 0.9, 4.0, itens, tamanho=CORPO + 2, espaco=14, marcadores=True)
    notas(s, "Resultado: 167 características (136 categorias e 31 atributos). O preço falta em 90% dos locais sem avaliação e em só 5% dos mais populares: usá-lo denunciaria a popularidade.")


# ---------------------------------------------------------------- 5. Treino e teste
def divisao(p):
    secao("divisao")
    slide_figura(p, "Divisão no tempo", "O modelo aprende com o passado e é medido no futuro", GRAFICOS / "divisao_tempo.png",
                 "Treino até 03/2019 · validação de 1 ano · teste a partir de 03/2020, usado uma única vez",
                 "Treino: 213.626 avaliações. Validação: 130.071, um ano inteiro para cobrir o verão. Teste: 85.925, 20% das avaliações. Os hiperparâmetros foram escolhidos na validação; o modelo final foi reajustado com treino e validação e medido uma vez no teste, que começa na pandemia.")
    slide_cartoes(p, "Quem é medido", "Cada cenário tem o seu público no teste", [
        (1, TERRACOTA, "Usuário antigo", "3 ou mais avaliações no treino"),
        (2, SALVIA, "Usuário novo", "Sem histórico; a 1ª avaliação simula o cadastro"),
        (3, MOSTARDA, "Local novo", "100 reais e 100 simulados, com as avaliações escondidas"),
    ], "Usuário novo: a primeira avaliação no teste informa a cidade e a categoria, como num cadastro, e as demais são o alvo. Local novo: os reais tiveram a 1ª avaliação depois do corte; os simulados são locais antigos com as avaliações escondidas.")


# ---------------------------------------------------------------- 6. Estimação
def estimacao(p):
    secao("estimacao")
    slide_numeros(p, "O que foi estimado", "Com treino + validação: 343.697 avaliações", [
        ("4,132", "nota média: o ponto de partida do escore", TERRACOTA),
        ("36,8", "avaliações de peso para a média geral", TERRACOTA),
        ("140.895", "perfis de usuário", SALVIA),
        ("167", "características no vocabulário", SALVIA),
        ("200 km", "alcance da localização", MOSTARDA),
        ("10", "regularização do viés na nota prevista", MOSTARDA),
    ], "Estimar o modelo, aqui, é calcular os escores, os perfis e o vocabulário a partir das avaliações, e escolher os hiperparâmetros na validação. Tudo foi congelado antes de abrir o teste.")
    slide_tabela(p, "Os pesos de cada cenário", "Escolhidos na validação e congelados antes do teste", [
        ["Cenário", "Conteúdo", "Escore", "Localização", "Popularidade"],
        ["Usuário antigo", "0,1", "0,2", "0,5", "0,2"],
        ["Usuário novo", "0,05", "0,19", "0,475", "0,285"],
        ["Local novo", "0,5", "—", "0,5", "—"],
    ], [0.28, 0.17, 0.15, 0.2, 0.2], "Usuário antigo: perfil centrado na média do usuário. Usuário novo: a categoria declarada entra com peso baixo, não como filtro. Local novo: perfil centrado na nota 3 e cota de 1 local novo na lista.",
       legenda="A localização tem o maior peso nos três cenários")
    slide_figura(p, "Como os pesos foram escolhidos", "Ganhar gosto custa conversão: a escolha cede 3,6%", GRAFICOS / "estimacao_pesos.png",
                 "Critério: conversão ≥ 95% da melhor e, entre essas, o maior gosto",
                 "Cada ponto é uma das 286 combinações de pesos testadas na validação. A escolhida, 0,1 / 0,2 / 0,5 / 0,2, tem conversão de 0,0739 e AUC de gosto de 0,5850.")
    slide_figura(p, "O papel de cada componente", "A localização traz a pessoa; o escore acerta o gosto", GRAFICOS / "estimacao_ablacao.png",
                 "Sem o escore, o gosto cai para 0,485; sem o conteúdo, empata",
                 "Ablação: tirar ou usar só um componente. Nenhum sozinho passa de 0,0415 de conversão. Sem o conteúdo, as métricas empatam: no cenário 1 ele amplia o catálogo.")
    slide_tabela(p, "Pesos do usuário novo", "Na validação, a cidade é o que mais ajuda; a categoria entra com peso baixo", [
        ["Método", "Conversão@10", "AUC de gosto"],
        ["Popularidade global", "0,0129", "0,4946"],
        ["Cidade + escore + popularidade", "0,0484", "0,5539"],
        ["+ categorias, peso 0,05 (escolhido)", "0,0484", "0,5541"],
        ["+ categorias como filtro", "0,0239", "0,5039"],
    ], [0.5, 0.25, 0.25], "Como filtro, as categorias derrubam a conversão: só 18,8% do que a pessoa avalia depois tem a categoria declarada.", destacar=3)
    slide_tabela(p, "Pesos do local novo", "Na validação, o perfil centrado em 3 fez o conteúdo ajudar", [
        ["Pontuação", "AUC de consumo"],
        ["Aleatória", "0,4994"],
        ["Só localização", "0,9195"],
        ["Conteúdo + localização, meio a meio (escolhida)", "0,9314"],
        ["Só conteúdo", "0,6351"],
    ], [0.7, 0.3], "Com o perfil centrado na média do usuário, o conteúdo sozinho ficava em 0,51. Centrado em 3, ele descreve o tipo de lugar que a pessoa frequenta. No teste, esse ganho não se confirmou.", destacar=3)


# ---------------------------------------------------------------- 7. Performance
def performance(p):
    secao("performance")
    s = novo_slide(p, "As métricas", "Duas perguntas: a pessoa foi? E gostou?")
    largura = (LARGURA - 2 * MARGEM - 0.3) / 2
    metricas = [("A pessoa foi?", "Taxa de conversão@10", "fração da lista avaliada depois com nota 4 ou mais", TERRACOTA),
                ("Ela gostou?", "AUC de gosto", "curva ROC: os locais bons acima dos ruins", SALVIA)]
    for k, (pergunta, nome, descricao, cor) in enumerate(metricas):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO)
        texto(s, x + 0.45, TOPO_CARTAO + 0.45, largura - 0.9, 0.6, pergunta, tamanho=22, cor=SUAVE, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 1.3, largura - 0.9, 1.4, nome, tamanho=30, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 2.9, largura - 0.9, 1.5, descricao, tamanho=CORPO + 2, espaco=0)
    notas(s, "Só usamos métricas vistas em aula. As duas competem: ordenar pela popularidade converte 7 vezes mais que o acaso, mas empata com ele no gosto. "
             "No cenário 3, a AUC de consumo: quem avaliou o local novo fica acima de quem não avaliou. De apoio: MAE, MSE e RMSE da nota, correlação de rankings, coberturas, novidade, serendipidade e diversidade. "
             "Toda comparação tem intervalo de confiança de 95%; se o intervalo inclui zero, é empate.")
    slide_figura(p, "Usuário antigo", "Empata com o óbvio na conversão e é o único que acerta o gosto", GRAFICOS / "performance_usuario_antigo.png",
                 "Modelo: conversão@10 de 0,052 e AUC de gosto de 0,554",
                 "No teste, com 5.663 usuários. Popularidade + local empata na conversão, mas fica abaixo do acaso no gosto (0,452). Vizinhos por item e PageRank convertem até 25% mais, também abaixo do acaso no gosto, e não atendem os cenários 2 e 3.")
    slide_figura(p, "Usuário novo", "Quase 5 vezes a popularidade global para quem nunca avaliou", GRAFICOS / "performance_usuario_novo.png",
                 "Conversão@10 de 0,045, contra 0,010 da popularidade",
                 "No teste, com 6.783 usuários; AUC de gosto de 0,560. A cidade informada é o que mais ajuda; a categoria com peso baixo empata e amplia o catálogo. 100% dos usuários recebem lista.")
    slide_figura(p, "Local novo", "Quem vai ao local novo fica bem acima dos demais", GRAFICOS / "performance_local_novo.png",
                 "AUC de consumo de 0,92 · o ganho do conteúdo sobre a localização não se confirmou",
                 "Nos 100 locais reais: 0,9209 contra 0,9173 só com a localização, empate. Nos simulados, +0,0044. A cota de 1 local novo leva de 21 para 126 as listas que acertam um local novo, com −0,0014 de conversão. O conteúdo pontua 100% dos locais novos; vizinhos e grafos, 0%.")
    slide_figura(p, "Curvas ROC no teste", "Gosto no usuário antigo e consumo nos locais novos", GRAFICOS / "performance_roc.png", None,
                 "A curva de gosto tem degraus porque a maioria dos usuários tem um ou dois locais bons e ruins no teste.")
    slide_numeros(p, "Previsão de nota", "O escore mais o viés do usuário tem o menor erro", [
        ("1,025", "RMSE com escore + viés", TERRACOTA),
        ("1,084", "RMSE só com o escore", SALVIA),
        ("1,134", "RMSE com a média global", TEXTO),
    ], "Em 21.121 avaliações do teste; MAE de 0,775. O erro de cerca de 1 ponto mostra o pouco espaço para personalizar a nota: por isso o modelo ordena, e a nota prevista entra na interface só como informação.")


# ---------------------------------------------------------------- 8. Interface
def interface(p):
    secao("interface")
    slide_cartoes(p, "Demonstração", "Três passos no app, ao vivo", [
        (1, TERRACOTA, "Demonstração", "Usuário #12.369: o gosto, o mapa e as prateleiras"),
        (2, SALVIA, "Usuário novo", "Cheyenne + cafeteria: o que foi usado e a lista"),
        (3, MOSTARDA, "Local novo", "Um local real: quem indicar e a decisão"),
    ], "Demonstração ao vivo de cerca de 2 minutos e meio, com o app aberto antes (streamlit run app.py). Se o app falhar, seguir pelas telas dos próximos slides.")
    slide_figura(p, "Recomendações em prateleiras", "Cada cartão traz a compatibilidade, a nota prevista e o porquê", RECORTES / "demo_prateleira.png",
                 "Aba Demonstração, Usuário #12.369", "A aba Demonstração mostra o gosto do usuário em gráficos e as recomendações em prateleiras, no estilo de catálogo: top para você, porque você gostou de X, novidades e bem avaliados perto de você.")
    slide_figura(p, "Usuário antigo na interface", "Cada local com as barras dos componentes e o porquê", RECORTES / "tela_antigo.png",
                 None, "Top 10 do Usuário #70.927 com a pontuação, a nota prevista, as barras de conteúdo, escore, localização e popularidade, e a explicação.")
    slide_figura(p, "Usuário novo na interface", "Tudo é opcional, e a lista nunca fica vazia", RECORTES / "tela_novo.png",
                 None, "Cheyenne, cafeteria e Wi-Fi: a interface diz o que foi usado e mostra a lista. Com poucos locais, avisa e amplia a busca.")
    slide_figura(p, "Local novo na interface", "Quem indicar e se o local entra na lista de alguém", RECORTES / "tela_local.png",
                 None, "Para um local novo real: os 10 usuários mais indicados, com o porquê, e a posição dele na lista de um usuário escolhido.")


# ---------------------------------------------------------------- 9. Conclusões
def conclusoes(p):
    secao("conclusoes")
    slide_cartoes(p, "Conclusões", "Uma técnica atende os três cenários", [
        ("✓", TERRACOTA, "Funcionou", "Três cenários com uma técnica; o melhor gosto entre as listas que convertem"),
        ("!", SALVIA, "Limites", "Pouca personalização; teste na pandemia; conteúdo sem ganho nos locais novos reais"),
        ("→", MOSTARDA, "Próximos passos", "Híbrido com vizinhos por item; texto das avaliações; teste com pessoas"),
    ], "A técnica de conteúdo e escores de produto atende os três cenários, com 100% de cobertura de usuários e de locais novos, e é a que melhor acerta o gosto entre as listas que convertem. "
       "Limites: a medida offline é uma aproximação; a correlação de rankings é de 0,07; o teste caiu na pandemia, e os metadados são de 2021; o ganho do conteúdo nos locais novos reais não se confirmou. Obrigado!")


# ---------------------------------------------------------------- Apêndice
def apendice(p):
    secao("apendice")
    s = p.slides.add_slide(p.slide_layouts[6])
    _fundo(s)
    circulo_branco(s)
    texto(s, 0.75, 2.6, 6.2, 1.2, "Apêndice", tamanho=54, cor=TERRACOTA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(s, 0.75, 3.85, 6.0, 0.8, "Detalhes para as perguntas", tamanho=20, cor=SALVIA, espaco=0)
    tracos(s, 0.75, 6.69)
    notas(s, "Slides de apoio para as perguntas.")

    slide_numeros(p, "O que os dados mostraram", "As análises que apoiam a técnica", [
        ("4", "locais em comum com o 20º vizinho de um usuário, mesmo no 5-core", TERRACOTA),
        ("11,5%", "da variância da nota explicada só pelo local", SALVIA),
        ("75%", "das avaliações de uma pessoa na cidade principal dela", MOSTARDA),
    ], "Vizinhos por usuário têm pouquíssima sobreposição; o local explica parte da nota (escore); as pessoas ficam na própria cidade (localização).")
    slide_figura(p, "Vizinhos por conteúdo", "Os 5 locais mais parecidos são do mesmo tipo", GRAFICOS / "teoria_vizinhos.png", None,
                 "Os vizinhos de uma pizzaria, de um café e de um bar, pelo cosseno. O cosseno mede o tipo de lugar, não a qualidade.")
    slide_figura(p, "Avaliações por ano", "A pandemia corta a série em 2020", GRAFICOS / "base_por_ano.png", None,
                 "As avaliações caem de 9.357 em fevereiro de 2020 para 906 em abril, e a coleta rareia em 2021.")
    slide_numeros(p, "Estabilidade", "A conversão cai à metade depois do 1º ano do teste", [
        ("0,050", "conversão no 1º ano do teste", TERRACOTA),
        ("0,024", "conversão depois do 1º ano", SALVIA),
    ], "A queda atinge todas as ordenações e acompanha a pandemia e a coleta rarefeita no fim da base. Da validação ao teste, a conversão do cenário 1 cai de 0,0739 para 0,0520.", colunas=2)
    for arquivo, titulo in [("inteira_antigo.png", "Tela inteira: usuário antigo"), ("inteira_novo.png", "Tela inteira: usuário novo"), ("inteira_local.png", "Tela inteira: local novo")]:
        slide_figura(p, titulo, None, RECORTES / arquivo, None, "Tela inteira da aba, gerada por scripts/capturar_telas.py.")


def main():
    preparar_recortes()
    p = Presentation()
    p.slide_width, p.slide_height = Inches(LARGURA), Inches(ALTURA)
    for montar in (capa, roteiro, sistema, base, teoria, tratamento, divisao, estimacao, performance, interface, conclusoes, apendice):
        montar(p)
    SAIDA.mkdir(exist_ok=True)
    p.save(ARQUIVO)
    print(f"{ARQUIVO.relative_to(RAIZ)}: {len(p.slides)} slides")


if __name__ == "__main__":
    main()
