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


def paineis(s, proporcoes, subtitulos=None, topo=TOPO_CARTAO, base=BASE_CARTAO):
    """Cartões lado a lado, com as larguras nas proporções dadas; devolve a área interna de cada um."""
    vao = 0.3
    util = LARGURA - 2 * MARGEM - vao * (len(proporcoes) - 1)
    areas, x = [], MARGEM
    for k, proporcao in enumerate(proporcoes):
        largura = util * proporcao
        cartao(s, x, topo, largura, base - topo)
        y = topo + 0.3
        if subtitulos and subtitulos[k]:
            texto(s, x + 0.35, y, largura - 0.7, 0.45, subtitulos[k], tamanho=18, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
            y += 0.6
        areas.append((x + 0.35, y, largura - 0.7, base - y - 0.3))
        x += largura + vao
    return areas


def leituras(s, area, itens, tamanho_valor=30):
    """Leituras de um gráfico: número (ou rótulo) em destaque e uma frase curta, empilhados na área."""
    x, y, w, h = area
    passo = h / len(itens)
    for k, (valor, frase, cor) in enumerate(itens):
        yk = y + k * passo
        if valor:
            texto(s, x, yk, w, 0.6, valor, tamanho=tamanho_valor, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
            texto(s, x, yk + 0.62, w, passo - 0.65, frase, tamanho=16, espaco=0)
        else:
            texto(s, x, yk, w, passo, frase, tamanho=17, cor=cor or TEXTO, negrito=True, espaco=0)


def slide_figura_leitura(p, titulo, mensagem, caminho, itens, fala, proporcao=0.66, tamanho_valor=30):
    """Gráfico à esquerda e, à direita, o que olhar nele (2 ou 3 leituras)."""
    s = novo_slide(p, titulo, mensagem)
    area_figura, area_leitura = paineis(s, [proporcao, 1 - proporcao])
    imagem(s, caminho, *area_figura)
    leituras(s, area_leitura, itens, tamanho_valor)
    notas(s, fala)
    return s


def slide_duas_figuras(p, titulo, mensagem, figuras, fala):
    """Dois gráficos lado a lado, cada um com uma frase embaixo."""
    s = novo_slide(p, titulo, mensagem)
    for (x, y, w, h), (caminho, frase) in zip(paineis(s, [0.5, 0.5]), figuras):
        base_figura = imagem(s, caminho, x, y, w, h - 0.8, topo=True)
        texto(s, x, base_figura + 0.25, w, 0.7, frase, tamanho=LEGENDA, negrito=True, espaco=0)
    notas(s, fala)
    return s


def slide_tela(p, titulo, mensagem, caminho, itens, fala):
    """Tela da interface na largura toda e, embaixo, uma faixa com três destaques numerados."""
    s = novo_slide(p, titulo, mensagem)
    altura_tela = 3.95
    cartao(s, MARGEM, TOPO_CARTAO, LARGURA - 2 * MARGEM, altura_tela)
    imagem(s, caminho, MARGEM + 0.3, TOPO_CARTAO + 0.2, LARGURA - 2 * MARGEM - 0.6, altura_tela - 0.4)
    y = TOPO_CARTAO + altura_tela + 0.25
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    for k, (_, frase, cor) in enumerate(itens):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, y, largura, BASE_CARTAO - y)
        circulo(s, x + 0.25, y + (BASE_CARTAO - y - 0.5) / 2, k + 1, cor, d=0.5)
        texto(s, x + 0.95, y, largura - 1.15, BASE_CARTAO - y, frase, tamanho=16, negrito=True, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
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
    s = novo_slide(p, "O sistema", "Recomendar onde comer a quem avalia no Google, em três situações")
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    cenarios = [(TERRACOTA, "Usuário antigo", "Uma lista a partir do histórico de notas"),
                (SALVIA, "Usuário novo", "Uma lista a partir do que a pessoa informa"),
                (MOSTARDA, "Local novo", "Para quais usuários indicar um local recém-aberto")]
    for k, (cor, nome, descricao) in enumerate(cenarios):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, 2.35)
        circulo(s, x + 0.3, TOPO_CARTAO + 0.3, k + 1, cor, d=0.6)
        texto(s, x + 1.1, TOPO_CARTAO + 0.38, largura - 1.3, 0.5, nome, tamanho=20, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 1.15, largura - 0.6, 1.0, descricao, tamanho=CORPO, espaco=0)
    y = TOPO_CARTAO + 2.7
    texto(s, MARGEM, y, 6, 0.4, "Como o sistema decide", tamanho=18, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    etapas = ["Avaliações e dados dos locais", "Características e escores do local", "Perfil do usuário", "Pontuação de cada local", "Lista com explicação"]
    largura, vao = 2.2, 0.38
    x0 = (LARGURA - (5 * largura + 4 * vao)) / 2
    y += 0.55
    for k, etapa in enumerate(etapas):
        x = x0 + k * (largura + vao)
        cartao(s, x, y, largura, 1.55, cor=TINTA_CARTAO)
        texto(s, x + 0.15, y, largura - 0.3, 1.55, etapa, tamanho=16, negrito=True, alinhar=PP_ALIGN.CENTER, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        if k < 4:
            seta(s, x + largura + 0.05, y + 0.78, x + largura + vao - 0.05, y + 0.78)
    notas(s, "O enunciado pede três cenários, e eles são frequentes na base: 66% dos usuários têm uma única avaliação, e de 51% a 57% das avaliações vêm de usuários novos. "
             "O sistema descreve cada local por suas características e escores, monta um perfil de cada usuário, pontua os locais e devolve os 10 primeiros, cada um com o porquê.")


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
    slide_figura_leitura(p, "As notas são altas", "A maioria das avaliações é positiva", GRAFICOS / "base_notas.png", [
        ("78%", "das avaliações são nota 4 ou 5", TERRACOTA),
        ("55,6%", "são nota 5", SALVIA),
        (None, "Por isso, no trabalho, \"relevante\" é nota 4 ou mais", TERRACOTA),
    ], "Notas de 1 a 3 são o sinal mais raro. Isso apoia considerar relevante a nota 4 ou mais, nas métricas de conversão e de gosto.")
    slide_duas_figuras(p, "Pouco histórico, atenção concentrada", "Há pouco sinal em comum entre usuários", [
        (GRAFICOS / "base_atividade.png", "66% dos usuários avaliaram um único local"),
        (GRAFICOS / "base_concentracao.png", "20% dos locais recebem 61% das avaliações"),
    ], "Só 10,4% dos usuários têm 5 ou mais avaliações, e a atenção se concentra nos locais populares (Gini de 0,587; o mais avaliado é o Texas Roadhouse de Cheyenne, com 2.598). "
       "Isso limita as técnicas colaborativas e torna importante o cenário de usuário novo.")
    slide_figura_leitura(p, "Categorias", "A nota varia conforme o tipo de local", GRAFICOS / "base_categorias.png", [
        ("74.061", "avaliações de fast food, a categoria mais avaliada", TERRACOTA),
        ("3,72", "a nota média de fast food, a menor entre as maiores", SALVIA),
        (None, "A qualidade do local é um sinal útil: o escore", TERRACOTA),
    ], "Cafe tem a maior nota (4,45). A nota varia por categoria, o que abre espaço para usar a qualidade do local como sinal.")
    slide_figura_leitura(p, "Cidades em ilhas", "As pessoas avaliam sobretudo na própria cidade", GRAFICOS / "base_mapa.png", [
        ("75%", "das avaliações de uma pessoa ficam na cidade principal dela", TERRACOTA),
        ("115", "cidades, em aglomerados com grandes vazios entre eles", SALVIA),
        (None, "A localização deve pesar na recomendação", TERRACOTA),
    ], "Cheyenne, Casper e Jackson concentram as avaliações. Os locais formam ilhas, e as pessoas ficam perto de onde costumam ir.", proporcao=0.6)


# ---------------------------------------------------------------- 3. Teoria
def teoria(p):
    secao("teoria")
    s = novo_slide(p, "Por que conteúdo e escores de produto", "É a única das quatro técnicas que atende os três cenários usando as notas")
    area_tabela, area_dados = paineis(s, [0.62, 0.38], ["As quatro técnicas", "O que os dados mostraram"])
    tabela(s, [
        ["Técnica", "Usuário novo", "Local novo"],
        ["Conteúdo e escores de produto", "Atende", "Atende"],
        ["Vizinhos próximos", "Não atende", "Não atende"],
        ["Bases de conhecimento", "Atende", "Sem usar as notas"],
        ["Redes e grafos", "Não atende", "Não atende"],
    ], area_tabela[0], area_tabela[1], area_tabela[2], 3.0, [0.46, 0.27, 0.27], tamanho=16, destacar=1)
    leituras(s, area_dados, [
        ("4", "locais em comum com o 20º vizinho de um usuário", TERRACOTA),
        ("11,5%", "da variância da nota vem do local", SALVIA),
        ("75%", "das avaliações na cidade principal", MOSTARDA),
    ], tamanho_valor=28)
    notas(s, "Vizinhos e grafos precisam de avaliações em comum, que o usuário novo e o local novo não têm. Bases de conhecimento não usariam as notas dos usuários. "
             "Os dados apoiam os componentes: vizinhos por usuário têm pouquíssima sobreposição; o local explica parte da nota, o que justifica o escore; e as pessoas ficam na própria cidade, o que justifica a localização.")

    s = novo_slide(p, "O método em uma ideia", "Para cada local, o sistema faz quatro perguntas e soma as respostas")
    perguntas = [(TERRACOTA, "É parecido com o que você gostou?", "Conteúdo"), (SALVIA, "É bom?", "Escore"),
                 (MOSTARDA, "É perto de onde você anda?", "Localização"), (TEXTO, "Muita gente vai?", "Popularidade")]
    largura = (LARGURA - 2 * MARGEM - 0.9) / 4
    for k, (cor, pergunta, nome) in enumerate(perguntas):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, 3.45)
        circulo(s, x + 0.3, TOPO_CARTAO + 0.3, k + 1, cor, d=0.6)
        texto(s, x + 0.3, TOPO_CARTAO + 1.1, largura - 0.6, 1.4, pergunta, tamanho=20, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 2.75, largura - 0.6, 0.5, nome, tamanho=CORPO, negrito=True, cor=cor if cor != TEXTO else SUAVE, espaco=0)
    y = TOPO_CARTAO + 3.75
    cartao(s, MARGEM, y, LARGURA - 2 * MARGEM, BASE_CARTAO - y)
    texto(s, MARGEM + 0.3, y + 0.2, LARGURA - 2 * MARGEM - 0.6, 1.4, [
        [("pontuação = α × conteúdo + β × escore + γ × localização + δ × popularidade", {"negrito": True, "cor": TERRACOTA, "tamanho": 22})],
        [("Cada resposta vai de 0 a 1. A lista são os 10 locais com maior pontuação, entre os abertos que a pessoa não avaliou.", {})],
    ], tamanho=16, alinhar=PP_ALIGN.CENTER, ancora=MSO_ANCHOR.MIDDLE, espaco=10)
    notas(s, "A primeira pergunta é o conteúdo; as outras três são os escores de produto, que descrevem o local em si. Os pesos α, β, γ e δ são escolhidos na validação (seção 6). Nos próximos slides, cada pergunta com um exemplo.")

    s = novo_slide(p, "Passo 1: o local vira uma lista", "Cada local é descrito pelas características que ele mesmo informa")
    area_exemplo, area_pesos = paineis(s, [0.62, 0.38], ["Exemplo com três locais", "Raras pesam mais (TF-IDF)"])
    linhas = [["Local"] + CARACTERISTICAS] + [[nome] + ["✓" if marca else "" for marca in vetor] for nome, vetor, _ in AVALIADOS]
    tabela(s, linhas, area_exemplo[0], area_exemplo[1], area_exemplo[2], 2.2, [0.22] + [0.156] * 5, tamanho=14)
    texto(s, area_exemplo[0], area_exemplo[1] + 2.7, area_exemplo[2], 1.2, "Na base real: 167 características, entre 136 categorias e 31 atributos (entrega, acessibilidade, pagamento…)", tamanho=16, espaco=0)
    leituras(s, area_pesos, [
        ("1,08", "peso de \"Entrega\": quase todo local tem", SUAVE),
        ("7,31", "peso de \"Loja de pretzel\": pouquíssimos têm", TERRACOTA),
    ], tamanho_valor=34)
    notas(s, "Cada coluna é uma característica, e cada local é uma linha: um vetor. Só entra o que um local recém-aberto poderia informar. O TF-IDF multiplica cada característica pelo quanto ela é rara; depois, cada vetor é normalizado para ter tamanho 1.")

    media, pesos, perfil, similaridades = exemplo_ana()
    s = novo_slide(p, "Passo 2: o usuário vira um perfil", f"A Ana avaliou três locais (média {br(media)}): ela gosta de pizzaria e não gosta de café")
    area_notas, area_perfil = paineis(s, [0.42, 0.58], ["As notas da Ana", "O perfil da Ana"])
    tabela(s, [["Local", "Nota", "Nota − média"]] + [[nome, str(nota), sinal(peso)] for (nome, _, nota), peso in zip(AVALIADOS, pesos)],
           area_notas[0], area_notas[1], area_notas[2], 1.9, [0.42, 0.22, 0.36], tamanho=15)
    texto(s, area_notas[0], area_notas[1] + 2.35, area_notas[2], 1.4, "Acima da própria média soma ao perfil; abaixo, subtrai", tamanho=16, negrito=True, cor=TERRACOTA, espaco=0)
    x, y, w, _ = area_perfil
    maior = max(abs(v) for v in perfil)
    meio = x + 2.3 + (w - 2.3) / 2
    meia = (w - 2.3) / 2 - 0.75
    for k, (nome, valor) in enumerate(zip(CARACTERISTICAS, perfil)):
        yk = y + 0.1 + k * 0.78
        texto(s, x, yk, 2.2, 0.5, nome, tamanho=16, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        comprimento = abs(valor) / maior * meia
        if comprimento > 0.01:
            retangulo(s, meio if valor > 0 else meio - comprimento, yk + 0.08, comprimento, 0.36, TERRACOTA if valor > 0 else SALVIA)
        xk = meio + comprimento + 0.08 if valor > 0 else meio - comprimento - 0.78
        texto(s, xk, yk, 0.7, 0.5, sinal(valor), tamanho=14, negrito=True, ancora=MSO_ANCHOR.MIDDLE, alinhar=PP_ALIGN.LEFT if valor > 0 else PP_ALIGN.RIGHT, espaco=0)
    linha = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(meio), Inches(y), Inches(meio), Inches(y + 5 * 0.78))
    linha.line.color.rgb = SUAVE
    linha.line.width = Pt(1.25)
    notas(s, "Cada local entra no perfil com o peso da nota menos a média da pessoa. A pizzaria soma 1,33; o café subtrai 1,67. 'Entrega' fica levemente negativa porque aparece na pizzaria, de que ela gostou, e no café, de que não gostou.")

    slide_figura_leitura(p, "O perfil de um usuário real", "Usuário #12.369, de Riverton: a mesma conta da Ana", GRAFICOS / "teoria_perfil_usuario.png", [
        ("Gosta mais", "restaurante americano, mesas ao ar livre, restaurante italiano", TERRACOTA),
        ("Gosta menos", "restaurante genérico, elevador acessível, drive-thru", SALVIA),
        (None, "É esse perfil que o cosseno compara com cada local", TEXTO),
    ], "O mesmo cálculo, num usuário real da base, como aparece na aba Demonstração da interface.", tamanho_valor=24)

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
    area_exemplos, area_grafico = paineis(s, [0.36, 0.64])
    x, y, w, h = area_exemplos
    for k, (avaliacoes, media_local, escore, cor) in enumerate([("2 avaliações", "média 5,0", "4,18", SALVIA), ("400 avaliações", "média 4,7", "4,65", TERRACOTA)]):
        yk = y + k * 2.2
        cartao(s, x - 0.1, yk, w + 0.2, 1.95, cor=TINTA_CARTAO)
        texto(s, x + 0.15, yk + 0.2, w - 0.3, 0.45, avaliacoes, tamanho=20, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.15, yk + 0.68, w - 0.3, 0.4, media_local, tamanho=16, cor=SUAVE, espaco=0)
        texto(s, x + 0.15, yk + 1.05, w - 0.3, 0.8, f"escore {escore}", tamanho=30, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(s, x, y + 4.5, w, 0.8, "Média geral: 4,13", tamanho=16, negrito=True, cor=TERRACOTA, espaco=0)
    imagem(s, GRAFICOS / "teoria_escore.png", *area_grafico)
    notas(s, "É a média bayesiana: escore = (v · média do local + m · 4,13) / (v + m), com m = 36,8 avaliações. Com poucas avaliações, o escore fica perto da média geral; com muitas, perto da média do próprio local. "
             "No gráfico, cada ponto é um local: os de cor clara, com poucas avaliações, ficam perto da linha de 4,13.")

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
    slide_figura_leitura(p, "Divisão no tempo", "O modelo aprende com o passado e é medido no futuro", GRAFICOS / "divisao_tempo.png", [
        ("até 03/2019", "treino: 213.626 avaliações", SALVIA),
        ("1 ano", "de validação, para cobrir o verão: julho tem 2 vezes o movimento de fevereiro", MOSTARDA),
        ("20%", "das avaliações no teste, a partir de 03/2020, usado uma única vez", TERRACOTA),
    ], "Os hiperparâmetros foram escolhidos na validação; o modelo final foi reajustado com treino e validação e medido uma vez no teste, que começa na pandemia e rareia no fim da coleta.", proporcao=0.64, tamanho_valor=26)
    slide_cartoes(p, "Quem é medido", "Cada cenário tem o seu público no teste", [
        (1, TERRACOTA, "Usuário antigo", "3 ou mais avaliações no treino"),
        (2, SALVIA, "Usuário novo", "Sem histórico; a 1ª avaliação simula o cadastro"),
        (3, MOSTARDA, "Local novo", "100 reais e 100 simulados, com as avaliações escondidas"),
    ], "Usuário novo: a primeira avaliação no teste informa a cidade e a categoria, como num cadastro, e as demais são o alvo. Local novo: os reais tiveram a 1ª avaliação depois do corte; os simulados são locais antigos com as avaliações escondidas.")


# ---------------------------------------------------------------- 6. Estimação
def estimacao(p):
    secao("estimacao")
    s = novo_slide(p, "O que foi estimado", "Com treino + validação (343.697 avaliações), e os pesos escolhidos na validação")
    area_numeros, area_pesos = paineis(s, [0.44, 0.56], ["Calculado das avaliações", "Pesos de cada cenário"])
    x, y, w, h = area_numeros
    estimados = [("4,132", "nota média: o ponto de partida do escore", TERRACOTA), ("36,8", "avaliações de peso para essa média", TERRACOTA),
                 ("140.895", "perfis de usuário", SALVIA), ("167", "características", SALVIA),
                 ("200 km", "alcance da localização", MOSTARDA), ("10", "regularização do viés", MOSTARDA)]
    for k, (valor, rotulo, cor) in enumerate(estimados):
        xk = x + (k % 2) * (w / 2)
        yk = y + (k // 2) * (h / 3)
        texto(s, xk, yk, w / 2 - 0.15, 0.55, valor, tamanho=26, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, xk, yk + 0.58, w / 2 - 0.15, h / 3 - 0.6, rotulo, tamanho=14, espaco=0)
    tabela(s, [
        ["Cenário", "Conteúdo", "Escore", "Localização", "Popularidade"],
        ["Usuário antigo", "0,1", "0,2", "0,5", "0,2"],
        ["Usuário novo", "0,05", "0,19", "0,475", "0,285"],
        ["Local novo", "0,5", "—", "0,5", "—"],
    ], area_pesos[0], area_pesos[1], area_pesos[2], 2.0, [0.26, 0.17, 0.14, 0.21, 0.22], tamanho=13)
    texto(s, area_pesos[0], area_pesos[1] + 2.4, area_pesos[2], 1.8, [
        [("A localização tem o maior peso nos três cenários.", {"negrito": True, "cor": TERRACOTA})],
        [("Tudo foi escolhido na validação e congelado antes do teste.", {})],
    ], tamanho=16, espaco=8)
    notas(s, "Estimar o modelo é calcular os escores, os perfis e o vocabulário a partir das avaliações e escolher os hiperparâmetros na validação. "
             "Usuário antigo: perfil centrado na média do usuário. Usuário novo: a categoria declarada entra com peso baixo, não como filtro. Local novo: perfil centrado na nota 3 e cota de 1 local novo na lista.")
    slide_figura_leitura(p, "Como os pesos foram escolhidos", "Ganhar gosto custa conversão: a escolha cede 3,6%", GRAFICOS / "estimacao_pesos.png", [
        ("0,0739", "conversão@10 da combinação escolhida", TERRACOTA),
        ("0,5850", "AUC de gosto da escolhida", SALVIA),
        (None, "Critério: conversão de ao menos 95% da melhor e, entre essas, o maior gosto", TEXTO),
    ], "Cada ponto é uma das 286 combinações de pesos testadas na validação. A escolhida, 0,1 / 0,2 / 0,5 / 0,2, cede 3,6% da melhor conversão em troca de mais gosto.", proporcao=0.62)
    slide_figura_leitura(p, "O papel de cada componente", "A localização traz a pessoa; o escore acerta o gosto", GRAFICOS / "estimacao_ablacao.png", [
        ("0,0415", "a melhor conversão de um componente sozinho", SALVIA),
        ("0,485", "AUC de gosto sem o escore: abaixo do acaso", TERRACOTA),
        (None, "Sem o conteúdo, as métricas empatam: ele amplia o catálogo", TEXTO),
    ], "Ablação: tirar ou usar só um componente. A combinação vale mais que as partes; sem o conteúdo, empata no cenário 1, onde ele amplia o catálogo.", proporcao=0.64)
    s = novo_slide(p, "Pesos dos outros cenários", "Na validação: a cidade guia o usuário novo; o perfil centrado em 3 guia o local novo")
    area_novo, area_local = paineis(s, [0.5, 0.5], ["Usuário novo", "Local novo"])
    tabela(s, [
        ["Método", "Conversão", "Gosto"],
        ["Popularidade global", "0,0129", "0,4946"],
        ["Cidade + escore + pop.", "0,0484", "0,5539"],
        ["+ categorias, peso 0,05", "0,0484", "0,5541"],
        ["+ categorias como filtro", "0,0239", "0,5039"],
    ], area_novo[0], area_novo[1], area_novo[2], 2.6, [0.52, 0.24, 0.24], tamanho=14, destacar=3)
    texto(s, area_novo[0], area_novo[1] + 3.05, area_novo[2], 1.3, "Escolhido: categorias com peso 0,05, não como filtro", tamanho=16, negrito=True, cor=TERRACOTA, espaco=0)
    tabela(s, [
        ["Pontuação", "AUC de consumo"],
        ["Aleatória", "0,4994"],
        ["Só localização", "0,9195"],
        ["Conteúdo + localização", "0,9314"],
        ["Só conteúdo", "0,6351"],
    ], area_local[0], area_local[1], area_local[2], 2.6, [0.64, 0.36], tamanho=14, destacar=3)
    texto(s, area_local[0], area_local[1] + 3.05, area_local[2], 1.3, "Escolhido: meio a meio, com o perfil centrado na nota 3", tamanho=16, negrito=True, cor=TERRACOTA, espaco=0)
    notas(s, "Usuário novo: como filtro, as categorias derrubam a conversão, porque só 18,8% do que a pessoa avalia depois tem a categoria declarada. "
             "Local novo: com o perfil centrado na média do usuário, o conteúdo sozinho ficava em 0,51; centrado em 3, ele descreve o tipo de lugar que a pessoa frequenta. No teste, esse ganho não se confirmou.")


# ---------------------------------------------------------------- 7. Performance
def performance(p):
    secao("performance")
    s = novo_slide(p, "As métricas", "Duas perguntas: a pessoa foi? E gostou?")
    largura = (LARGURA - 2 * MARGEM - 0.3) / 2
    metricas = [("A pessoa foi?", "Taxa de conversão@10", "fração da lista avaliada depois com nota 4 ou mais", TERRACOTA),
                ("Ela gostou?", "AUC de gosto", "curva ROC: os locais bons acima dos ruins", SALVIA)]
    for k, (pergunta, nome, descricao, cor) in enumerate(metricas):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO - 1.1)
        texto(s, x + 0.45, TOPO_CARTAO + 0.45, largura - 0.9, 0.6, pergunta, tamanho=22, cor=SUAVE, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 1.25, largura - 0.9, 1.0, nome, tamanho=30, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.45, TOPO_CARTAO + 2.4, largura - 0.9, 1.2, descricao, tamanho=CORPO + 2, espaco=0)
    texto(s, MARGEM, BASE_CARTAO - 0.8, LARGURA - 2 * MARGEM, 0.7,
          "Também: AUC de consumo (local novo), RMSE e MAE da nota, coberturas, novidade e diversidade · IC de 95% em toda comparação",
          tamanho=16, cor=SUAVE, alinhar=PP_ALIGN.CENTER, espaco=0)
    notas(s, "Só usamos métricas vistas em aula. As duas competem: ordenar pela popularidade converte 7 vezes mais que o acaso, mas empata com ele no gosto. "
             "Toda comparação tem intervalo de confiança de 95% por bootstrap; se o intervalo inclui zero, é empate.")
    slide_figura_leitura(p, "Usuário antigo", "Empata com o óbvio na conversão e é o único que acerta o gosto", GRAFICOS / "performance_usuario_antigo.png", [
        ("0,052", "conversão@10 do modelo, em empate com popularidade + local", TERRACOTA),
        ("0,554", "AUC de gosto: o único acima do acaso entre os que convertem", SALVIA),
        ("+25%", "de conversão nos vizinhos por item, mas abaixo do acaso no gosto", MOSTARDA),
    ], "No teste, com 5.663 usuários. Popularidade + local fica em 0,452 de gosto. As técnicas colaborativas convertem mais para usuários antigos, mas não atendem os cenários 2 e 3.", proporcao=0.64)
    slide_figura_leitura(p, "Usuário novo", "Quase 5 vezes a popularidade global para quem nunca avaliou", GRAFICOS / "performance_usuario_novo.png", [
        ("0,045", "conversão@10, contra 0,010 da popularidade global", TERRACOTA),
        ("0,560", "AUC de gosto", SALVIA),
        ("100%", "dos usuários recebem lista, mesmo sem informar nada", MOSTARDA),
    ], "No teste, com 6.783 usuários. A cidade informada é o que mais ajuda; a categoria com peso baixo empata e amplia o catálogo; como filtro, derruba a conversão.", proporcao=0.64)
    slide_figura_leitura(p, "Local novo", "Quem vai ao local novo fica bem acima dos demais", GRAFICOS / "performance_local_novo.png", [
        ("0,921", "AUC de consumo nos 100 locais novos reais", TERRACOTA),
        ("empate", "com só a localização (0,917): o ganho do conteúdo não se confirmou", SALVIA),
        ("21 → 126", "listas que acertam um local novo, com a cota de 1 vaga", MOSTARDA),
    ], "Nos simulados, o conteúdo soma 0,0044. A cota custa 0,0014 de conversão. O conteúdo pontua 100% dos locais novos; vizinhos e grafos, 0%.", proporcao=0.62, tamanho_valor=28)
    s = novo_slide(p, "Curvas ROC e previsão de nota", "O gosto e o consumo na curva; a nota prevista erra cerca de 1 ponto")
    area_roc, area_nota = paineis(s, [0.66, 0.34], [None, "Previsão de nota (RMSE)"])
    imagem(s, GRAFICOS / "performance_roc.png", *area_roc)
    leituras(s, area_nota, [
        ("1,025", "escore + viés do usuário", TERRACOTA),
        ("1,084", "só o escore", SALVIA),
        ("1,134", "média global", TEXTO),
    ], tamanho_valor=30)
    notas(s, "À esquerda, as curvas ROC médias por usuário: a de gosto tem degraus porque a maioria tem um ou dois locais bons e ruins no teste. À direita, o RMSE da nota prevista em 21.121 avaliações do teste (MAE de 0,775). "
             "O erro de cerca de 1 ponto mostra o pouco espaço para personalizar a nota: por isso o modelo ordena, e a nota prevista entra na interface só como informação.")


# ---------------------------------------------------------------- 8. Interface
def interface(p):
    secao("interface")
    s = novo_slide(p, "Demonstração", "Três passos no app, ao vivo")
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    passos = [(TERRACOTA, "Demonstração", "Usuário #12.369: o gosto, o mapa e as prateleiras"),
              (SALVIA, "Usuário novo", "Cheyenne + cafeteria: o que foi usado e a lista"),
              (MOSTARDA, "Local novo", "Um local real: quem indicar e a decisão")]
    for k, (cor, nome, descricao) in enumerate(passos):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, 1.75)
        circulo(s, x + 0.3, TOPO_CARTAO + 0.3, k + 1, cor, d=0.55)
        texto(s, x + 1.0, TOPO_CARTAO + 0.35, largura - 1.2, 0.45, nome, tamanho=18, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 1.0, largura - 0.6, 0.7, descricao, tamanho=15, espaco=0)
    y = TOPO_CARTAO + 2.05
    cartao(s, MARGEM, y, LARGURA - 2 * MARGEM, BASE_CARTAO - y)
    imagem(s, RECORTES / "demo_prateleira.png", MARGEM + 0.35, y + 0.25, LARGURA - 2 * MARGEM - 0.7, BASE_CARTAO - y - 0.5)
    notas(s, "Demonstração ao vivo de cerca de 2 minutos e meio, com o app aberto antes (streamlit run app.py). Embaixo, a aba Demonstração: as recomendações em prateleiras, cada cartão com a compatibilidade, a nota prevista e o porquê. "
             "Se o app falhar, seguir pelas telas dos próximos slides.")
    for arquivo, titulo, mensagem, itens, fala in [
        ("tela_antigo.png", "Usuário antigo na interface", "O top 10 com o porquê de cada local",
         [(None, "Pontuação e nota prevista", TERRACOTA), (None, "Barras dos quatro componentes", SALVIA), (None, "\"Porque você gostou de X\"", MOSTARDA)],
         "Top 10 do Usuário #70.927, com a pontuação, a nota prevista, as barras de conteúdo, escore, localização e popularidade, e a explicação."),
        ("tela_novo.png", "Usuário novo na interface", "Tudo é opcional, e a lista nunca fica vazia",
         [(None, "Cidade, preço, categorias, atributos e um local de exemplo", TERRACOTA), (None, "Mostra o que foi usado", SALVIA), (None, "Avisa e amplia a busca quando faltam locais", MOSTARDA)],
         "Cheyenne, cafeteria e Wi-Fi: a interface diz o que foi usado e mostra a lista."),
        ("tela_local.png", "Local novo na interface", "Quem indicar e se o local entra na lista de alguém",
         [(None, "Os 10 usuários mais indicados, com o porquê", TERRACOTA), (None, "A posição do local na lista de um usuário", SALVIA), (None, "A decisão: recomendar ou não", MOSTARDA)],
         "Para um local novo real: os usuários mais indicados e a posição dele na lista de um usuário escolhido."),
    ]:
        slide_tela(p, titulo, mensagem, RECORTES / arquivo, itens, fala)


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

    slide_figura(p, "Vizinhos por conteúdo", "Os 5 locais mais parecidos são do mesmo tipo", GRAFICOS / "teoria_vizinhos.png", None,
                 "Os vizinhos de uma pizzaria, de um café e de um bar, pelo cosseno. O cosseno mede o tipo de lugar, não a qualidade.")
    slide_figura(p, "Avaliações por mês", "Julho tem 2 vezes o movimento de fevereiro", GRAFICOS / "base_por_mes.png", None,
                 "De 2017 a 2019; 3,29 vezes nas cidades turísticas. Por isso a validação cobre um ano inteiro.")
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
