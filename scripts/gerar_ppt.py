"""Gera a apresentação do Trabalho T1 em `apresentacao/T1_Sistema_Recomendacao.pptx`.

O visual segue o modelo da usuária no Canva (fundo bege, títulos em terracota, cartões brancos).
As fontes do modelo (Montserrat e Inter) não estão instaladas, então os títulos usam Century Gothic
e o texto, Arial; no Canva, volta-se às originais. Os números vêm do `relatório.md`.

    python scripts/gerar_ppt.py
"""

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
FIGURAS = RAIZ / "figuras"
SAIDA = RAIZ / "apresentacao"
RECORTES = SAIDA / "imagens"
ARQUIVO = SAIDA / "T1_Sistema_Recomendacao.pptx"

# ---------------------------------------------------------------- Tema (do modelo do Canva)
FUNDO = RGBColor(0xED, 0xE7, 0xDD)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)
TERRACOTA = RGBColor(0xB4, 0x4E, 0x1C)
SALVIA = RGBColor(0x69, 0x79, 0x67)
MOSTARDA = RGBColor(0xCC, 0x8B, 0x20)
TEXTO = RGBColor(0x33, 0x3F, 0x48)
SUAVE = RGBColor(0x6B, 0x75, 0x7D)
TINTA_CARTAO = RGBColor(0xF6, 0xF2, 0xEC)
FONTE_TITULO = "Century Gothic"
FONTE_TEXTO = "Arial"

LARGURA, ALTURA = 13.333, 7.5
MARGEM = 0.39
TOPO_CARTAO = 1.6
BASE_CARTAO = 7.08


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


def _marcador(paragrafo, caractere="•", cor=TERRACOTA):
    pPr = paragrafo._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.25)))
    pPr.set("indent", str(-Inches(0.22)))
    for filho in list(pPr):
        if filho.tag in (qn("a:buNone"), qn("a:buChar"), qn("a:buClr")):
            pPr.remove(filho)
    clr = etree.SubElement(pPr, qn("a:buClr"))
    srgb = etree.SubElement(clr, qn("a:srgbClr"))
    srgb.set("val", str(cor))
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", caractere)


def texto(slide, x, y, w, h, linhas, tamanho=16, cor=TEXTO, fonte=FONTE_TEXTO, negrito=False, alinhar=PP_ALIGN.LEFT,
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


def figura_com_legenda(slide, caminho, area, legenda, tamanho=14):
    """Figura no topo da área e a legenda logo abaixo dela."""
    x, y, w, h = area
    base = imagem(slide, caminho, x, y, w, h - 0.75, topo=True)
    texto(slide, x, base + 0.2, w, 0.7, legenda, tamanho=tamanho, espaco=0)


def notas(slide, fala):
    slide.notes_slide.notes_text_frame.text = fala


def circulo_numerado(slide, x, y, numero, cor, d=0.5):
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
    r.text = str(numero)
    r.font.name = FONTE_TITULO
    r.font.bold = True
    r.font.size = Pt(18 * d / 0.5)
    r.font.color.rgb = BRANCO


def seta(slide, x1, y1, x2, y2, cor=SALVIA):
    linha = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    linha.line.color.rgb = cor
    linha.line.width = Pt(2)
    ln = linha.line._get_or_add_ln()
    cauda = etree.SubElement(ln, qn("a:tailEnd"))
    cauda.set("type", "triangle")
    return linha


def destaque(slide, x, y, w, valor, rotulo, cor=TERRACOTA, tamanho=34):
    texto(slide, x, y, w, 0.65, valor, tamanho=tamanho, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(slide, x, y + 0.68, w, 0.6, rotulo, tamanho=13, cor=SUAVE, espaco=0)


# ---------------------------------------------------------------- Layouts do modelo
ITENS = {
    "b": "b. Descrição do sistema",
    "c": "c. Base de dados",
    "d": "d. Conceitos teóricos do modelo",
    "e": "e. Tratamento dos dados",
    "f": "f. Treino e teste",
    "g": "g. Estimação do modelo",
    "h": "h. Performance do modelo",
    "i": "i. Interface nos 3 cenários",
}
_ITEM = {"atual": None}


def item(chave):
    """Define o item do enunciado dos próximos slides; ele aparece no rodapé."""
    _ITEM["atual"] = ITENS.get(chave, chave)


def novo_slide(apresentacao, titulo, mensagem=None):
    """Layout de conteúdo: título em terracota, a mensagem em sálvia e o item do enunciado no rodapé."""
    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    _fundo(slide)
    if _ITEM["atual"]:
        texto(slide, LARGURA - MARGEM - 5.0, 7.16, 5.0, 0.25, _ITEM["atual"], tamanho=11, cor=SUAVE, alinhar=PP_ALIGN.RIGHT, espaco=0)
    texto(slide, MARGEM, 0.28, LARGURA - 2 * MARGEM, 0.75, titulo, tamanho=36, cor=TERRACOTA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    if mensagem:
        texto(slide, MARGEM, 0.98, LARGURA - 2 * MARGEM, 0.5, mensagem, tamanho=18, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    return slide


def dois_cartoes(slide, subtitulos, proporcao=0.5, topo=TOPO_CARTAO):
    """Dois cartões lado a lado, com subtítulo em sálvia dentro de cada um; devolve as áreas internas."""
    vao = 0.3
    util = LARGURA - 2 * MARGEM - vao
    larguras = [util * proporcao, util * (1 - proporcao)]
    areas, x = [], MARGEM
    for largura, subtitulo in zip(larguras, subtitulos):
        cartao(slide, x, topo, largura, BASE_CARTAO - topo)
        y = topo + 0.25
        if subtitulo:
            texto(slide, x + 0.3, y, largura - 0.6, 0.45, subtitulo, tamanho=18, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
            y += 0.55
        areas.append((x + 0.3, y, largura - 0.6, BASE_CARTAO - y - 0.25))
        x += largura + vao
    return areas


def cartao_cheio(slide, subtitulo=None, topo=TOPO_CARTAO):
    cartao(slide, MARGEM, topo, LARGURA - 2 * MARGEM, BASE_CARTAO - topo)
    y = topo + 0.25
    if subtitulo:
        texto(slide, MARGEM + 0.3, y, LARGURA - 2 * MARGEM - 0.6, 0.45, subtitulo, tamanho=18, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
        y += 0.55
    return (MARGEM + 0.3, y, LARGURA - 2 * MARGEM - 0.6, BASE_CARTAO - y - 0.25)


def tracos(slide, x, y):
    for i, cor in enumerate([TERRACOTA, SALVIA, MOSTARDA]):
        forma = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + i * 0.67), Inches(y), Inches(0.53), Inches(0.09))
        forma.fill.solid()
        forma.fill.fore_color.rgb = cor
        _sem_borda(forma)


def divisoria(apresentacao, titulo, subtitulo):
    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    _fundo(slide)
    circulo = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.0), Inches(-0.82), Inches(8.87), Inches(8.87))
    circulo.fill.solid()
    circulo.fill.fore_color.rgb = BRANCO
    _sem_borda(circulo)
    texto(slide, 0.75, 2.6, 6.2, 1.2, titulo, tamanho=54, cor=TERRACOTA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(slide, 0.75, 3.85, 6.0, 0.8, subtitulo, tamanho=17, cor=SALVIA, espaco=0)
    tracos(slide, 0.75, 6.69)
    return slide


# ---------------------------------------------------------------- Recortes das telas
def preparar_recortes():
    RECORTES.mkdir(parents=True, exist_ok=True)
    demo = Image.open(FIGURAS / "50_demonstracao.png")
    recortes = {
        "demo_perfil.png": (demo, (360, 300, 1740, 800)),
        "demo_prateleira.png": (demo, (360, 1180, 1740, 1520)),
        "demo_gosto.png": (demo, (360, 470, 1170, 790)),
        "tela_antigo.png": (Image.open(FIGURAS / "51_usuario_antigo.png"), (370, 640, 1140, 1090)),
        "tela_novo.png": (Image.open(FIGURAS / "52_usuario_novo.png"), (370, 250, 1180, 1010)),
        "tela_local.png": (Image.open(FIGURAS / "53_local_novo.png"), (370, 330, 1250, 1150)),
        "inteira_antigo.png": (Image.open(FIGURAS / "51_usuario_antigo.png"), (360, 90, 1740, 1130)),
        "inteira_novo.png": (Image.open(FIGURAS / "52_usuario_novo.png"), (360, 90, 1740, 1210)),
        "inteira_local.png": (Image.open(FIGURAS / "53_local_novo.png"), (360, 90, 1740, 1160)),
    }
    for nome, (origem, caixa) in recortes.items():
        origem.crop(caixa).save(RECORTES / nome)


# ---------------------------------------------------------------- Slides
def capa(p):
    slide = p.slides.add_slide(p.slide_layouts[6])
    _fundo(slide)
    circulo = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.0), Inches(-0.82), Inches(8.87), Inches(8.87))
    circulo.fill.solid()
    circulo.fill.fore_color.rgb = BRANCO
    _sem_borda(circulo)
    imagem(slide, FIGURAS / "16_mapa_locais.png", 7.75, 1.2, 5.2, 5.0)
    texto(slide, 0.75, 0.68, 6.5, 0.4, "PUCRS · Sistemas de Recomendação · Prof. Rafael Scopel, PhD", tamanho=14, cor=TERRACOTA, espaco=0)
    texto(slide, 0.75, 1.55, 6.3, 2.6, ["Onde comer", "em Wyoming"], tamanho=58, cor=TERRACOTA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(slide, 0.75, 4.05, 6.0, 0.9, "Recomendação por conteúdo e escores de produto", tamanho=20, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    texto(slide, 0.75, 5.3, 6.0, 0.9, ["Integrantes: [a definir]", "Novembro de 2026"], tamanho=14, cor=TEXTO, espaco=4)
    tracos(slide, 0.75, 6.69)
    notas(slide, "Apresentar o grupo e o tema: um sistema que recomenda restaurantes, cafés e bares de Wyoming a partir das avaliações do Google, com a técnica de conteúdo e escores de produto.")


def roteiro(p):
    item(None)
    s = novo_slide(p, "Roteiro", "A apresentação segue os itens pedidos no enunciado")
    nomes = [
        ("b", "Descrição do sistema"), ("c", "Base de dados"), ("d", "Conceitos teóricos do modelo"),
        ("e", "Tratamento dos dados"), ("f", "Treino e teste"), ("g", "Estimação do modelo"),
        ("h", "Performance do modelo"), ("i", "Interface nos 3 cenários"), ("→", "Conclusões"),
    ]
    cores = [TERRACOTA, SALVIA, MOSTARDA]
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    altura = (BASE_CARTAO - TOPO_CARTAO - 0.6) / 3
    for k, (letra, nome) in enumerate(nomes):
        coluna, linha = k % 3, k // 3
        x = MARGEM + coluna * (largura + 0.3)
        y = TOPO_CARTAO + linha * (altura + 0.3)
        cartao(s, x, y, largura, altura)
        circulo_numerado(s, x + 0.3, y + (altura - 0.6) / 2, letra, cores[k % 3], d=0.6)
        texto(s, x + 1.1, y, largura - 1.3, altura, nome, tamanho=18, negrito=True, fonte=FONTE_TITULO, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
    notas(s, "A apresentação segue a ordem dos itens do enunciado, de b a i; o item a é a capa. O rodapé de cada slide indica o item que ele cobre.")


def sistema(p):
    item("b")
    s = novo_slide(p, "O sistema", "Recomendar onde comer a quem avalia no Google, em três situações")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Os três cenários", "Como o sistema decide"], proporcao=0.47)
    cenarios = [
        (TERRACOTA, "Usuário antigo", "Lista de locais a partir do histórico de notas"),
        (SALVIA, "Usuário novo", "Lista a partir do que a pessoa informa: cidade, gostos, um local de exemplo"),
        (MOSTARDA, "Local novo", "Para quais usuários antigos indicar um local recém-cadastrado"),
    ]
    for i, (cor, nome, descricao) in enumerate(cenarios):
        y = y1 + 0.1 + i * 1.45
        cartao(s, x1, y, w1, 1.25, cor=TINTA_CARTAO)
        circulo_numerado(s, x1 + 0.2, y + 0.37, i + 1, cor)
        texto(s, x1 + 0.9, y + 0.17, w1 - 1.1, 0.4, nome, tamanho=17, negrito=True, cor=TEXTO, fonte=FONTE_TITULO, espaco=0)
        texto(s, x1 + 0.9, y + 0.55, w1 - 1.1, 0.65, descricao, tamanho=14, cor=TEXTO, espaco=0)
    etapas = ["Avaliações + dados dos locais", "Vetor de conteúdo e escores de cada local", "Perfil do usuário", "Pontuação com 4 componentes", "Lista com explicação, na interface"]
    altura = 0.5
    for i, etapa in enumerate(etapas):
        y = y2 + 0.05 + i * 0.72
        forma = cartao(s, x2, y, w2, altura, cor=TINTA_CARTAO)
        texto(s, x2 + 0.25, y, w2 - 0.5, altura, etapa, tamanho=15, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        if i < len(etapas) - 1:
            seta(s, x2 + w2 / 2, y + altura, x2 + w2 / 2, y + 0.72)
    texto(s, x2, y2 + 3.75, w2, 0.9,
          [[("s(u, i) = α·conteúdo + β·escore + γ·localização + δ·popularidade", {"negrito": True, "cor": TERRACOTA})]],
          tamanho=14, alinhar=PP_ALIGN.CENTER)
    notas(s, "O enunciado pede três cenários, e eles são frequentes na base: 66% dos usuários têm uma única avaliação, e de 51% a 57% das avaliações vêm de usuários novos. "
             "Escolhemos a técnica de conteúdo e escores de produto. A pontuação de cada local soma quatro componentes; cada recomendação vem com o porquê ('porque você gostou de X') e com as barras dos componentes.")


def base(p):
    item("c")
    s = novo_slide(p, "A base", "Google Local 2021: 430 mil avaliações de restaurantes, cafés e bares, com nota por usuário")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Em números", "78% das notas são 4 ou 5"], proporcao=0.42)
    numeros = [("429.622", "avaliações"), ("175.278", "usuários"), ("1.863", "locais"), ("115", "cidades"), ("2008–2021", "período"), ("99,87%", "esparsidade")]
    for i, (valor, rotulo) in enumerate(numeros):
        coluna, linha = i % 2, i // 2
        destaque(s, x1 + coluna * w1 / 2, y1 + 0.05 + linha * 1.3, w1 / 2 - 0.1, valor, rotulo, cor=TERRACOTA if i < 2 else TEXTO, tamanho=30)
    texto(s, x1, y1 + h1 - 0.45, w1, 0.45, "Fonte: McAuley Lab (UCSD), estado de Wyoming, recorte de alimentação", tamanho=11, cor=SUAVE, espaco=0)
    figura_com_legenda(s, FIGURAS / "10_distribuicao_notas.png", (x2, y2, w2, h2), "Nota 5 sozinha: 55,6%. Relevante, no trabalho, é nota 4 ou mais.")
    notas(s, "A base atende a exigência do enunciado: cada avaliação tem usuário e nota. São 429.622 avaliações de 175.278 usuários em 1.863 locais. "
             "A matriz usuário × local está 99,87% vazia. As notas são altas: 78% são 4 ou 5, por isso consideramos relevante a nota 4 ou mais.")


def historico(p):
    s = novo_slide(p, "Usuários e locais", "Pouco histórico por pessoa, atenção concentrada em poucos locais")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["66% têm uma única avaliação", "20% dos locais têm 61% das avaliações"], proporcao=0.42)
    figura_com_legenda(s, FIGURAS / "11_atividade_usuarios.png", (x1, y1, w1, h1), "Só 10,4% dos usuários têm 5 ou mais avaliações.")
    figura_com_legenda(s, FIGURAS / "12_popularidade.png", (x2, y2, w2, h2), "Índice de Gini de 0,587; o mais avaliado é o Texas Roadhouse de Cheyenne (2.598).")
    notas(s, "Dois fatos que limitam qualquer técnica baseada em histórico em comum: a maioria das pessoas tem uma avaliação só, e a atenção se concentra nos locais populares. Isso pesa na escolha da técnica e na importância do cenário de usuário novo.")


def categorias(p):
    s = novo_slide(p, "Categorias e cidades", "Fast food é o mais avaliado e o pior avaliado; as cidades formam ilhas")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["As 20 categorias com mais avaliações", "Locais no mapa, pela nota média"], proporcao=0.55)
    figura_com_legenda(s, FIGURAS / "14_categorias.png", (x1, y1, w1, h1), "Fast food: 74.061 avaliações e nota 3,72. Cafe: a maior nota, 4,45.")
    figura_com_legenda(s, FIGURAS / "16_mapa_locais.png", (x2, y2, w2, h2), "Cheyenne, Casper e Jackson à frente; grandes vazios entre as cidades.")
    notas(s, "A nota varia por categoria, o que abre espaço para o escore de qualidade. No mapa, os locais formam aglomerados isolados: a localização deve pesar na recomendação, e 75% das avaliações de uma pessoa ficam na cidade principal dela.")


def tecnica(p):
    item("d")
    s = novo_slide(p, "Por que conteúdo e escores de produto", "É a única das quatro técnicas que atende sozinha os três cenários usando as notas")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["As quatro técnicas do enunciado", "O que as análises mostraram"], proporcao=0.58)
    linhas = [
        ("Técnica", "Usuário novo", "Local novo"),
        ("Conteúdo e escores de produto", "Atende", "Atende"),
        ("Vizinhos próximos", "Não atende", "Não atende"),
        ("Bases de conhecimento", "Atende", "Sem personalização"),
        ("Redes e grafos", "Sem arestas", "Sem arestas"),
    ]
    tabela = s.shapes.add_table(len(linhas), 3, Inches(x1), Inches(y1 + 0.1), Inches(w1), Inches(3.4)).table
    tabela.columns[0].width = Inches(w1 * 0.46)
    tabela.columns[1].width = Inches(w1 * 0.27)
    tabela.columns[2].width = Inches(w1 * 0.27)
    for i, linha in enumerate(linhas):
        for j, valor in enumerate(linha):
            celula = tabela.cell(i, j)
            celula.fill.solid()
            celula.fill.fore_color.rgb = TERRACOTA if i == 0 else (TINTA_CARTAO if i == 1 else BRANCO)
            quadro = celula.text_frame
            quadro.text = valor
            fonte = quadro.paragraphs[0].runs[0].font
            fonte.name = FONTE_TEXTO
            fonte.size = Pt(15)
            fonte.bold = i == 0 or i == 1
            cor = BRANCO if i == 0 else (SALVIA if valor == "Atende" else (TERRACOTA if valor in ("Não atende", "Sem arestas") else TEXTO))
            fonte.color.rgb = cor
            celula.vertical_anchor = MSO_ANCHOR.MIDDLE
    texto(s, x1, y1 + 3.8, w1, 1.2, "Vizinhos e grafos precisam de avaliações em comum, que o usuário novo e o local novo não têm; bases de conhecimento não usariam as notas.", tamanho=14, cor=SUAVE)
    fatos = [("4", "locais em comum com o 20º vizinho de um usuário, mesmo no 5-core"), ("11,5%", "da variância da nota explicada só pelo local"), ("75%", "das avaliações de uma pessoa na cidade principal dela")]
    for i, (valor, rotulo) in enumerate(fatos):
        destaque(s, x2, y2 + 0.1 + i * 1.5, w2, valor, rotulo, cor=[TERRACOTA, SALVIA, MOSTARDA][i])
    notas(s, "A técnica é a única que atende sozinha os três cenários usando as notas. As análises apoiam os componentes: vizinhos por usuário têm pouquíssima sobreposição; o local explica parte da nota, o que justifica o escore de qualidade; e as pessoas ficam na própria cidade, o que justifica o componente de localização.")


def tabela_simples(slide, linhas, x, y, w, h, larguras, tamanho=13, alinhar_centro=True):
    """Tabela no estilo do modelo: cabeçalho em terracota e linhas alternadas."""
    tabela = slide.shapes.add_table(len(linhas), len(linhas[0]), Inches(x), Inches(y), Inches(w), Inches(h)).table
    for j, fracao in enumerate(larguras):
        tabela.columns[j].width = Inches(w * fracao)
    for i, linha in enumerate(linhas):
        for j, valor in enumerate(linha):
            celula = tabela.cell(i, j)
            celula.fill.solid()
            celula.fill.fore_color.rgb = TERRACOTA if i == 0 else (TINTA_CARTAO if i % 2 == 0 else BRANCO)
            celula.text_frame.text = valor
            celula.margin_left = celula.margin_right = Inches(0.06)
            paragrafo = celula.text_frame.paragraphs[0]
            paragrafo.alignment = PP_ALIGN.CENTER if (alinhar_centro and j > 0) else PP_ALIGN.LEFT
            if not paragrafo.runs:
                continue
            fonte = paragrafo.runs[0].font
            fonte.name, fonte.size, fonte.bold = FONTE_TEXTO, Pt(tamanho), i == 0 or j == 0
            fonte.color.rgb = BRANCO if i == 0 else TEXTO
            celula.vertical_anchor = MSO_ANCHOR.MIDDLE
    return tabela


def num(valor, casas=2):
    return f"{valor:+.{casas}f}".replace(".", ",") if casas and valor != 0 else f"{valor:.{casas}f}".replace(".", ",")


def br(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


# Exemplo de brinquedo dos passos 1 a 3: a usuária Ana e três locais. Contas feitas aqui, sem TF-IDF,
# para o slide mostrar números que fecham.
CARACTERISTICAS = ["Pizzaria", "Café", "Bar", "Entrega", "Mesas ao ar livre"]
AVALIADOS = [("Pizzaria A", [1, 0, 0, 1, 0], 5), ("Café B", [0, 1, 0, 1, 0], 2), ("Bar C", [0, 0, 1, 0, 1], 4)]
CANDIDATOS = [("Pizzaria D", [1, 0, 0, 1, 0]), ("Café E", [0, 1, 0, 0, 1])]


def _exemplo():
    media = np.mean([nota for _, _, nota in AVALIADOS])
    pesos = [nota - media for _, _, nota in AVALIADOS]
    perfil = sum(peso * np.array(vetor, float) for peso, (_, vetor, _) in zip(pesos, AVALIADOS))
    similaridades = []
    for nome, vetor in CANDIDATOS:
        v = np.array(vetor, float)
        cosseno = perfil @ v / (np.linalg.norm(perfil) * np.linalg.norm(v))
        similaridades.append((nome, cosseno, (cosseno + 1) / 2))
    return media, pesos, perfil, similaridades


def ideia(p):
    s = novo_slide(p, "O método em uma ideia", "Para cada local, o sistema faz quatro perguntas e soma as respostas")
    perguntas = [
        ("1", TERRACOTA, "É parecido com o que você gostou?", "Conteúdo", "compara as características do local com o seu perfil"),
        ("2", SALVIA, "É bom?", "Escore", "a nota média do local, com cuidado para quem tem poucas avaliações"),
        ("3", MOSTARDA, "É perto de onde você anda?", "Localização", "a distância até os locais que você já avaliou"),
        ("4", TEXTO, "Muita gente vai?", "Popularidade", "quantas avaliações o local tem"),
    ]
    largura = (LARGURA - 2 * MARGEM - 0.9) / 4
    for k, (numero, cor, pergunta, nome, explicacao) in enumerate(perguntas):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, 3.7)
        circulo_numerado(s, x + 0.3, TOPO_CARTAO + 0.3, numero, cor, d=0.6)
        texto(s, x + 0.3, TOPO_CARTAO + 1.1, largura - 0.6, 1.0, pergunta, tamanho=18, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 2.15, largura - 0.6, 0.4, nome, tamanho=15, negrito=True, cor=cor if cor != TEXTO else SUAVE, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 2.55, largura - 0.6, 1.0, explicacao, tamanho=13, espaco=0)
    y = TOPO_CARTAO + 4.0
    cartao(s, MARGEM, y, LARGURA - 2 * MARGEM, BASE_CARTAO - y)
    texto(s, MARGEM + 0.4, y + 0.25, LARGURA - 2 * MARGEM - 0.8, BASE_CARTAO - y - 0.4, [
        [("Cada resposta vira uma nota de 0 a 1, e a pontuação é a soma com pesos:", {})],
        [("pontuação = α·conteúdo + β·escore + γ·localização + δ·popularidade", {"negrito": True, "cor": TERRACOTA, "tamanho": 20})],
        [("A lista são os 10 locais com maior pontuação, entre os abertos que a pessoa ainda não avaliou.", {})],
    ], tamanho=15, espaco=8, alinhar=PP_ALIGN.CENTER, ancora=MSO_ANCHOR.MIDDLE)
    notas(s, "A ideia do método cabe em quatro perguntas. A primeira é o 'conteúdo': o local se parece com os que a pessoa gostou? As outras três são os 'escores de produto', que descrevem o local em si: se é bom, se é perto e se é popular. "
             "Cada resposta vira um número de 0 a 1, e a pontuação final é uma soma ponderada. Nos próximos slides, cada pergunta com um exemplo.")


def passo_vetor(p):
    s = novo_slide(p, "Passo 1: o local vira uma lista de características", "Categorias e atributos que o próprio local informa, com mais peso para os raros")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Exemplo com três locais", "Raras pesam mais (TF-IDF)"], proporcao=0.58)
    linhas = [["Local"] + CARACTERISTICAS] + [[nome] + ["✓" if marca else "" for marca in vetor] for nome, vetor, _ in AVALIADOS]
    tabela_simples(s, linhas, x1, y1 + 0.1, w1, 2.0, [0.22] + [0.156] * 5, tamanho=13)
    texto(s, x1, y1 + 2.45, w1, 2.3, [
        "Cada coluna é uma característica, e cada local é uma linha: um vetor.",
        "Na base real são 167 características: 136 categorias (pizzaria, café, churrascaria…) e 31 atributos (entrega, acessibilidade, formas de pagamento…).",
        "Só entra o que um local recém-aberto poderia informar.",
    ], tamanho=15, espaco=10, marcadores=True)
    destaque(s, x2, y2 + 0.1, w2, "1,08", "peso de \"Entrega\": quase todo local tem, então diz pouco sobre ele", cor=SUAVE, tamanho=32)
    destaque(s, x2, y2 + 1.6, w2, "7,31", "peso de \"Loja de pretzel\": rara, então diz muito", cor=TERRACOTA, tamanho=32)
    texto(s, x2, y2 + 3.2, w2, 1.6, "O TF-IDF multiplica cada característica pelo quanto ela é rara na base. Depois, cada vetor é normalizado para ter tamanho 1.", tamanho=14, espaco=0)
    notas(s, "O primeiro passo é descrever cada local por suas características, como numa planilha de marcações: cada coluna é uma característica, e cada local é uma linha. "
             "Nem toda característica informa o mesmo: quase todo restaurante faz entrega, então isso diz pouco; ser uma loja de pretzel diz muito. O TF-IDF dá esse peso: 1,08 para entrega e 7,31 para loja de pretzel, na nossa base.")


def passo_perfil(p):
    media, pesos, perfil, _ = _exemplo()
    s = novo_slide(p, "Passo 2: o usuário vira um perfil", "O perfil soma os locais que a pessoa avaliou, com peso pela nota em relação à média dela")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, [f"Exemplo: Ana avaliou três locais (média {br(media)})", "Perfil real do Usuário #12.369"], proporcao=0.55)
    linhas = [["Local", "Nota", "Nota − média"]] + [[nome, str(nota), num(peso)] for (nome, _, nota), peso in zip(AVALIADOS, pesos)]
    tabela_simples(s, linhas, x1, y1 + 0.05, w1, 1.6, [0.4, 0.25, 0.35], tamanho=14)
    texto(s, x1, y1 + 1.85, w1, 0.4, "Perfil da Ana: soma das características, com esses pesos", tamanho=14, negrito=True, espaco=0)
    maior = max(abs(v) for v in perfil)
    base = y1 + 2.35
    meio = x1 + 2.6 + (w1 - 2.6) / 2
    for k, (nome, valor) in enumerate(zip(CARACTERISTICAS, perfil)):
        y = base + k * 0.48
        texto(s, x1, y, 2.5, 0.38, nome, tamanho=13, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        comprimento = abs(valor) / maior * ((w1 - 2.6) / 2 - 0.55)
        if comprimento > 0.01:
            barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(meio if valor > 0 else meio - comprimento), Inches(y + 0.06), Inches(comprimento), Inches(0.26))
            barra.fill.solid()
            barra.fill.fore_color.rgb = TERRACOTA if valor > 0 else SALVIA
            _sem_borda(barra)
        posicao = meio + comprimento + 0.08 if valor > 0 else meio - comprimento - 0.62
        texto(s, posicao, y, 0.6, 0.38, num(valor), tamanho=12, ancora=MSO_ANCHOR.MIDDLE, alinhar=PP_ALIGN.LEFT if valor > 0 else PP_ALIGN.RIGHT, espaco=0)
    linha = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(meio), Inches(base - 0.05), Inches(meio), Inches(base + 5 * 0.48))
    linha.line.color.rgb = SUAVE
    linha.line.width = Pt(1)
    figura_com_legenda(s, RECORTES / "demo_gosto.png", (x2, y2, w2, h2), "Lado direito: gosta mais que a própria média. Lado esquerdo: gosta menos.", tamanho=13)
    notas(s, "O segundo passo é o perfil. A Ana deu 5 para uma pizzaria, 2 para um café e 4 para um bar; a média dela é 3,67. Cada local entra no perfil com o peso da nota menos a média: a pizzaria soma 1,33, o café subtrai 1,67. "
             "O resultado diz que a Ana gosta de pizzaria e não gosta de café; 'Entrega' fica levemente negativa porque aparece nos dois. À direita, o perfil real de um usuário da base, calculado do mesmo jeito.")


def passo_cosseno(p):
    _, _, _, similaridades = _exemplo()
    s = novo_slide(p, "Passo 3: \"parecido\" é o cosseno", "Compara o perfil com cada local candidato: perto de 1 é parecido, perto de 0 é o oposto")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Os candidatos da Ana", "Na base real: vizinhos de três locais"], proporcao=0.45)
    for k, ((nome, vetor), (_, cosseno, similaridade)) in enumerate(zip(CANDIDATOS, similaridades)):
        y = y1 + 0.1 + k * 1.85
        cartao(s, x1, y, w1, 1.6, cor=TINTA_CARTAO)
        tem = ", ".join(c for c, marca in zip(CARACTERISTICAS, vetor) if marca)
        texto(s, x1 + 0.25, y + 0.15, w1 - 2.2, 0.4, nome, tamanho=17, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x1 + 0.25, y + 0.6, w1 - 2.2, 0.9, f"tem: {tem}", tamanho=13, espaco=0)
        destaque(s, x1 + w1 - 1.85, y + 0.2, 1.7, br(similaridade), "conteúdo", cor=TERRACOTA if similaridade > 0.5 else SALVIA, tamanho=30)
    texto(s, x1, y1 + 3.9, w1, 1.0, [[("conteúdo = (cosseno + 1) / 2", {"negrito": True, "cor": TERRACOTA})], [("O cosseno mede o ângulo entre os dois vetores; a conta leva o resultado para 0 a 1.", {})]], tamanho=14, espaco=6)
    imagem(s, FIGURAS / "20_vizinhos_conteudo.png", x2, y2, w2, h2)
    notas(s, "O terceiro passo compara o perfil com cada candidato pelo cosseno: dois vetores que apontam para o mesmo lado dão 1; para lados opostos, menos 1; a conta leva para 0 a 1. "
             f"A Pizzaria D, parecida com o que a Ana gostou, recebe {br(similaridades[0][2])}; o Café E recebe {br(similaridades[1][2])}. "
             "À direita, na base real, os vizinhos de uma pizzaria, de um café e de um bar são do mesmo tipo. Atenção: o cosseno mede o tipo de lugar, não a qualidade; é por isso que entram os escores.")


def passo_escores(p):
    s = novo_slide(p, "Passo 4: os escores do local", "Qualidade, distância e popularidade, cada um de 0 a 1")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Escore: média bayesiana", "Localização e popularidade"], proporcao=0.52)
    texto(s, x1, y1, w1, 0.9, "Puxa a média de quem tem poucas avaliações para a média geral (4,13), com peso m = 36,8 avaliações:", tamanho=14, espaco=0)
    texto(s, x1, y1 + 0.75, w1, 0.5, "escore = (v · média do local + m · 4,13) / (v + m)", tamanho=15, negrito=True, cor=TERRACOTA, espaco=0)
    exemplos = [("2 avaliações, média 5,0", "4,18", "pouca evidência: fica perto de 4,13"), ("400 avaliações, média 4,7", "4,65", "muita evidência: fica perto de 4,7")]
    for k, (caso, valor, leitura) in enumerate(exemplos):
        y = y1 + 1.5 + k * 1.55
        cartao(s, x1, y, w1, 1.35, cor=TINTA_CARTAO)
        texto(s, x1 + 0.25, y + 0.15, w1 - 2.0, 0.45, caso, tamanho=15, negrito=True, espaco=0)
        texto(s, x1 + 0.25, y + 0.65, w1 - 2.0, 0.6, leitura, tamanho=13, cor=SUAVE, espaco=0)
        destaque(s, x1 + w1 - 1.6, y + 0.15, 1.5, valor, "escore", cor=SALVIA if k == 0 else TERRACOTA, tamanho=30)
    texto(s, x2, y2, w2, 0.5, [[("Localização = média de exp(−km / 200)", {"negrito": True, "cor": TERRACOTA})]], tamanho=15, espaco=0)
    texto(s, x2, y2 + 0.45, w2, 0.5, "até os locais que a pessoa já avaliou:", tamanho=14, espaco=0)
    distancias = [("0 km", "1,00"), ("50 km", "0,78"), ("200 km", "0,37"), ("500 km", "0,08")]
    tabela_simples(s, [["Distância", "Localização"]] + [list(d) for d in distancias], x2, y2 + 0.95, w2, 2.0, [0.5, 0.5], tamanho=14)
    texto(s, x2, y2 + 3.25, w2, 1.6, [
        [("Popularidade = log(1 + avaliações) / log(1 + máximo)", {"negrito": True, "cor": TERRACOTA})],
        [("O logaritmo evita que os gigantes dominem: 100 avaliações já dão 0,59; 2.598, o máximo, dá 1.", {})],
    ], tamanho=14, espaco=6)
    notas(s, "Os escores de produto descrevem o local. O escore de qualidade é uma média bayesiana: com poucas avaliações, ele fica perto da média geral de 4,13; com muitas, fica perto da média do próprio local. "
             "A localização vale 1 para um local ao lado dos que a pessoa frequenta e cai com a distância. A popularidade usa logaritmo, para não ser dominada pelos maiores.")


def passo_soma(p):
    s = novo_slide(p, "Passo 5: a soma decide a ordem", "Exemplo real, Usuário #12.369 de Riverton: o melhor escore da base fica em 375º por estar longe")
    pesos = [("Conteúdo", 0.1, TERRACOTA), ("Escore", 0.2, SALVIA), ("Localização", 0.5, MOSTARDA), ("Popularidade", 0.2, SUAVE)]
    casos = [
        ("The Depot Restaurant (Riverton)", "1º de 1.508", [0.551, 0.840, 0.691, 0.777]),
        ("Bar J Chuckwagon Suppers (Wilson)", "375º de 1.508", [0.476, 0.941, 0.260, 0.880]),
    ]
    x, w = MARGEM, LARGURA - 2 * MARGEM
    cartao(s, x, TOPO_CARTAO, w, BASE_CARTAO - TOPO_CARTAO)
    linhas = [["Componente", "Peso"] + [nome.split(" (")[0] for nome, _, _ in casos]]
    for k, (nome, peso, _) in enumerate(pesos):
        linhas.append([nome, br(peso, 1)] + [f"{br(valores[k])} × {br(peso, 1)} = {br(peso * valores[k], 3)}" for _, _, valores in casos])
    linhas.append(["Pontuação", "", *[br(sum(peso * v for (_, peso, _), v in zip(pesos, valores)), 3) for _, _, valores in casos]])
    tabela_simples(s, linhas, x + 0.3, TOPO_CARTAO + 0.3, w - 0.6, 2.6, [0.2, 0.1, 0.35, 0.35], tamanho=14)
    escala = (w - 6.2) / 0.75
    for k, (nome, posicao, valores) in enumerate(casos):
        y = TOPO_CARTAO + 3.3 + k * 1.0
        texto(s, x + 0.3, y, 3.4, 0.5, nome.split(" (")[0], tamanho=14, negrito=True, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        inicio = x + 3.8
        for (componente, peso, cor), valor in zip(pesos, valores):
            largura = peso * valor * escala
            barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(inicio), Inches(y + 0.05), Inches(largura), Inches(0.4))
            barra.fill.solid()
            barra.fill.fore_color.rgb = cor
            barra.line.color.rgb = BRANCO
            barra.line.width = Pt(1.5)
            barra.shadow.inherit = False
            inicio += largura
        texto(s, inicio + 0.15, y, 1.9, 0.5, posicao, tamanho=14, negrito=True, cor=TERRACOTA, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
    legenda_y = TOPO_CARTAO + 5.25
    inicio = x + 3.8
    for componente, _, cor in pesos:
        quadrado = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(inicio), Inches(legenda_y + 0.08), Inches(0.2), Inches(0.2))
        quadrado.fill.solid()
        quadrado.fill.fore_color.rgb = cor
        _sem_borda(quadrado)
        texto(s, inicio + 0.28, legenda_y, 1.6, 0.36, componente, tamanho=12, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        inicio += 1.9
    notas(s, "O quinto passo soma tudo com os pesos. Exemplo real: para o Usuário #12.369, de Riverton, o The Depot Restaurant tem escore bom, é perto e é popular: soma 0,724 e fica em 1º. "
             "O Bar J Chuckwagon Suppers tem o melhor escore da base, mas fica em Wilson, longe dos lugares que essa pessoa avalia: a localização cai para 0,26, e ele fica em 375º. É a localização, com peso 0,5, que mais move a ordem.")


def passo_cenarios(p):
    s = novo_slide(p, "Os três cenários usam a mesma conta", "O que muda é de onde vem o perfil e quais perguntas têm resposta")
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    blocos = [
        ("1", TERRACOTA, "Usuário antigo", ["Perfil: o histórico de notas", "As quatro perguntas", "Na lista, 1 vaga reservada a um local novo"]),
        ("2", SALVIA, "Usuário novo", ["Perfil: o que a pessoa informa (categorias, atributos, um local de que gosta)", "Localização: distância ao centro da cidade informada", "Tudo é opcional; a lista nunca fica vazia"]),
        ("3", MOSTARDA, "Local novo", ["Sem avaliações: não há escore nem popularidade", "Só conteúdo e localização, meio a meio", "Ordena os usuários antigos para indicar o local"]),
    ]
    for k, (numero, cor, nome, itens) in enumerate(blocos):
        x = MARGEM + k * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO - 1.15)
        circulo_numerado(s, x + 0.3, TOPO_CARTAO + 0.3, numero, cor, d=0.55)
        texto(s, x + 1.0, TOPO_CARTAO + 0.35, largura - 1.2, 0.45, nome, tamanho=18, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 1.15, largura - 0.6, 3.3, itens, tamanho=15, espaco=12, marcadores=True)
    y = BASE_CARTAO - 0.9
    cartao(s, MARGEM, y, LARGURA - 2 * MARGEM, 0.9, cor=TINTA_CARTAO)
    texto(s, MARGEM + 0.3, y, LARGURA - 2 * MARGEM - 0.6, 0.9, [[("Nota prevista: ", {"negrito": True}), ("escore do local + o quanto a pessoa costuma dar acima ou abaixo da média (viés). Aparece na interface como informação.", {})]], tamanho=14, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
    notas(s, "Os três cenários usam a mesma pontuação. Para o usuário novo, o perfil vem do que ele informa, e a localização é a distância ao centro da cidade escolhida. "
             "Para o local novo, que não tem avaliações, só há resposta para duas perguntas: é parecido e é perto. Por isso o conteúdo é o que permite recomendar um local recém-aberto.")


def tratamento(p):
    item("e")
    s = novo_slide(p, "Tratamento dos dados", "Do arquivo bruto à base limpa, e o que entra no vetor de conteúdo")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Duplicados e ausentes", "O vetor de conteúdo"], proporcao=0.58)
    linhas = [
        ("Problema", "Quanto", "Tratamento"),
        ("Local repetido (mesmo gmap_id)", "72 cópias", "Removido"),
        ("Avaliação duplicada", "4.296", "Removida"),
        ("Local sem categoria", "85", "Removido"),
        ("Nota ou usuário ausente", "0", "Removeria"),
        ("Avaliação sem texto", "41,3%", "Mantida: texto não entra"),
        ("Local sem preço", "37,1%", "Fora do vetor; filtro"),
        ("Local sem cidade", "7", "Usa a coordenada"),
        ("Local fechado", "238", "Não é recomendado"),
    ]
    tabela = s.shapes.add_table(len(linhas), 3, Inches(x1), Inches(y1), Inches(w1), Inches(3.9)).table
    for j, fracao in enumerate([0.46, 0.18, 0.36]):
        tabela.columns[j].width = Inches(w1 * fracao)
    for i, linha in enumerate(linhas):
        for j, valor in enumerate(linha):
            celula = tabela.cell(i, j)
            celula.fill.solid()
            celula.fill.fore_color.rgb = TERRACOTA if i == 0 else (TINTA_CARTAO if i % 2 == 0 else BRANCO)
            celula.text_frame.text = valor
            celula.margin_left = celula.margin_right = Inches(0.08)
            fonte = celula.text_frame.paragraphs[0].runs[0].font
            fonte.name, fonte.size, fonte.bold = FONTE_TEXTO, Pt(13), i == 0
            fonte.color.rgb = BRANCO if i == 0 else TEXTO
            celula.vertical_anchor = MSO_ANCHOR.MIDDLE
    texto(s, x1, y1 + 4.05, w1, 0.8, [[("Recorte: ", {"negrito": True}), ("12.016 locais → 1.863 de alimentação, pela categoria principal; 429.622 avaliações na base limpa.", {})]], tamanho=13, espaco=0)
    texto(s, x2, y2, w2, h2, [
        [("Entra: ", {"negrito": True, "cor": SALVIA}), ("categorias e atributos declaráveis (serviço, acessibilidade, comodidades, pagamento, planejamento)", {})],
        [("Fica fora: ", {"negrito": True, "cor": TERRACOTA}), ("atributos que vêm do comportamento dos clientes (\"popular para\", público, ambiente) e os da pandemia", {})],
        [("Fica fora: ", {"negrito": True, "cor": TERRACOTA}), ("preço, que falta em 90% dos locais sem avaliação e em 5% dos populares", {})],
        [("Fica fora: ", {"negrito": True, "cor": TERRACOTA}), ("texto das avaliações, que um local novo não tem", {})],
        [("Resultado: ", {"negrito": True}), ("167 tokens (136 de categorias e 31 de atributos)", {})],
    ], tamanho=15, espaco=12, marcadores=True)
    notas(s, "Duplicados: 72 cópias idênticas de locais e 4.296 avaliações repetidas, removidas; não havia avaliação repetida do mesmo usuário no mesmo local. Ausentes: nenhuma nota ou usuário faltando; 85 locais sem categoria saíram; texto, preço e cidade ausentes ficaram, com o tratamento da tabela. O recorte usa a categoria principal: um hotel com restaurante fica de fora. "
             "No vetor, a regra é só usar o que um local recém-cadastrado poderia informar; atributos derivados do comportamento dos clientes e o preço carregam viés de popularidade.")


def divisao(p):
    item("f")
    s = novo_slide(p, "Treino e teste", "Divisão no tempo: o modelo aprende com o passado e é medido no futuro")
    cartao(s, MARGEM, TOPO_CARTAO, LARGURA - 2 * MARGEM, 3.15)
    imagem(s, FIGURAS / "21_divisao_temporal.png", MARGEM + 0.3, TOPO_CARTAO + 0.15, 7.2, 2.85)
    texto(s, MARGEM + 7.8, TOPO_CARTAO + 0.3, 4.5, 2.7, [
        [("Treino: ", {"negrito": True}), ("até 31/03/2019 (213.626)", {})],
        [("Validação: ", {"negrito": True}), ("1 ano inteiro, para cobrir o verão (130.071)", {})],
        [("Teste: ", {"negrito": True}), ("a partir de 31/03/2020, 20% das avaliações (85.925)", {})],
        [("O teste foi usado uma única vez, com tudo congelado.", {"negrito": True, "cor": TERRACOTA})],
    ], tamanho=14, espaco=9, marcadores=True)
    y = TOPO_CARTAO + 3.4
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    blocos = [
        (TERRACOTA, "Usuário antigo", "3 ou mais avaliações no treino; o alvo são as avaliações depois do corte."),
        (SALVIA, "Usuário novo", "Sem histórico; a 1ª avaliação simula o cadastro (cidade e categoria), e as demais são o alvo."),
        (MOSTARDA, "Local novo", "Naturais: 1ª avaliação depois do corte (100 no teste). Simulados: 100 locais com as avaliações escondidas."),
    ]
    for i, (cor, nome, descricao) in enumerate(blocos):
        x = MARGEM + i * (largura + 0.3)
        cartao(s, x, y, largura, BASE_CARTAO - y)
        circulo_numerado(s, x + 0.25, y + 0.25, i + 1, cor, d=0.45)
        texto(s, x + 0.85, y + 0.3, largura - 1.0, 0.4, nome, tamanho=16, negrito=True, fonte=FONTE_TITULO, espaco=0)
        texto(s, x + 0.25, y + 0.85, largura - 0.5, BASE_CARTAO - y - 1.0, descricao, tamanho=13, espaco=0)
    notas(s, "A divisão respeita o tempo: os hiperparâmetros foram escolhidos na validação, e o modelo final foi reajustado com treino e validação e medido uma vez no teste. "
             "Atenção: o teste começa na pandemia, com queda forte de avaliações em abril de 2020, e a coleta rareia em 2021. Cada cenário tem o seu público: usuários antigos, novos e locais novos, reais e simulados.")


def metricas(p):
    item("h")
    s = novo_slide(p, "Métricas estudadas em aula", "Duas perguntas, duas métricas: a pessoa foi? E gostou?")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["A pessoa foi?", "Ela gostou?"])
    destaque(s, x1, y1 + 0.1, w1, "Taxa de conversão@10", "fração da lista de 10 que a pessoa avaliou depois com nota 4 ou mais", cor=TERRACOTA, tamanho=26)
    destaque(s, x2, y2 + 0.1, w2, "AUC de gosto (curva ROC)", "entre os locais que a pessoa avaliou, a chance de um bom (4 ou 5) ficar acima de um ruim", cor=SALVIA, tamanho=26)
    texto(s, x1, y1 + 1.75, w1, 2.4, [
        [("Exemplo que justifica as duas: ", {"negrito": True})],
        [("ordenar pela popularidade converte 7 vezes mais que o acaso (0,0204 × 0,0028), mas empata com ele no gosto (0,486 × 0,497).", {})],
        [("Converter mede aonde a pessoa vai, não se ela gostou.", {"negrito": True, "cor": TERRACOTA})],
    ], tamanho=15, espaco=8)
    texto(s, x2, y2 + 1.75, w2, 2.6, [
        [("No cenário 3: ", {"negrito": True}), ("AUC de consumo (quem avaliou o local novo fica acima de quem não avaliou).", {})],
        [("De apoio: ", {"negrito": True}), ("MAE, MSE e RMSE da nota, correlação de rankings, coberturas, novidade, serendipidade e diversidade.", {})],
        [("Toda comparação com intervalo de confiança de 95% (bootstrap); se inclui zero, é empate.", {"negrito": True, "cor": SALVIA})],
    ], tamanho=15, espaco=8)
    notas(s, "Usamos só as métricas vistas em aula. A conversão mede se a pessoa foi a um local da lista e o avaliou bem; a AUC de gosto mede se o modelo põe os locais de que ela gostou acima dos que ela não gostou. "
             "As duas competem: a popularidade converte muito e não acerta o gosto. Por isso o critério de escolha usa as duas.")


def modelo_estimado(p):
    item("g")
    s = novo_slide(p, "Estimação", "O modelo final, ajustado com treino + validação (343.697 avaliações)")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["O que foi estimado", "Pesos escolhidos na validação"], proporcao=0.47)
    estimados = [("4,132", "C: nota média, o prior do escore"), ("36,8", "m: peso do prior (percentil 25)"),
                 ("140.895", "perfis de usuário"), ("167", "tokens no vocabulário TF-IDF"),
                 ("200 km", "τ: alcance da localização"), ("10", "regularização do viés na nota prevista")]
    for k, (valor, rotulo) in enumerate(estimados):
        coluna, linha = k % 2, k // 2
        destaque(s, x1 + coluna * w1 / 2, y1 + 0.05 + linha * 1.4, w1 / 2 - 0.15, valor, rotulo, cor=[TERRACOTA, SALVIA, MOSTARDA][linha], tamanho=28)
    linhas = [("Cenário", "Conteúdo", "Escore", "Localização", "Popularidade"),
              ("1. Usuário antigo", "0,1", "0,2", "0,5", "0,2"),
              ("2. Usuário novo", "0,05", "0,19", "0,475", "0,285"),
              ("3. Local novo", "0,5", "—", "0,5", "—")]
    tabela_simples(s, [list(linha) for linha in linhas], x2, y2 + 0.05, w2, 2.0, [0.24, 0.16, 0.14, 0.22, 0.24], tamanho=12)
    texto(s, x2, y2 + 2.3, w2, 2.6, [
        [("Usuário antigo: ", {"negrito": True}), ("perfil centrado na média do usuário.", {})],
        [("Usuário novo: ", {"negrito": True}), ("a categoria declarada entra com peso baixo, não como filtro.", {})],
        [("Local novo: ", {"negrito": True}), ("perfil centrado na nota 3 e cota de 1 local novo na lista.", {})],
        [("Tudo foi escolhido na validação e congelado antes do teste.", {"negrito": True, "cor": TERRACOTA})],
    ], tamanho=14, espaco=8, marcadores=True)
    notas(s, "Estimar o modelo, aqui, é calcular os escores, os perfis e o vocabulário a partir das avaliações, e escolher os hiperparâmetros na validação. "
             "O modelo final foi reajustado com treino e validação: nota média de 4,132 como prior do escore, com peso m de 36,8; 140.895 perfis; 167 tokens. "
             "Os pesos de cada cenário vêm do critério que mostramos a seguir. Tudo foi congelado antes de abrir o teste.")


def pesos(p):
    s = novo_slide(p, "Escolha dos pesos", "Os pesos trocam 3,6% de conversão por mais gosto; o escore é quem acerta o gosto")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["286 combinações de pesos na validação", "Ablação: tirar ou usar só um componente"], proporcao=0.47)
    imagem(s, FIGURAS / "31_grade_pesos.png", x1, y1, w1, h1 - 0.9)
    texto(s, x1, y1 + h1 - 0.8, w1, 0.8, [[("Critério: ", {"negrito": True}), ("taxa de conversão@10 ≥ 95% da melhor; entre essas, a maior AUC de gosto. Escolhido: 0,1 / 0,2 / 0,5 / 0,2 (conversão 0,0739; gosto 0,5850).", {})]], tamanho=13, espaco=0)
    imagem(s, FIGURAS / "32_ablacao.png", x2, y2, w2, h2 - 1.1)
    texto(s, x2, y2 + h2 - 1.0, w2, 1.0, [
        [("Nenhum componente sozinho passa de 0,0415 de conversão; ", {}), ("sem o escore, o gosto cai para 0,485", {"negrito": True}), ("; sem o conteúdo, empata — ele amplia o catálogo.", {})],
    ], tamanho=13, espaco=0)
    notas(s, "Cada ponto do gráfico é uma combinação de pesos. Conversão e gosto competem: subir um custa o outro. O critério aceita perder até 5% da melhor conversão e escolhe o maior gosto; a escolha cede 3,6%. "
             "A ablação mostra o papel de cada componente: localização e popularidade trazem a conversão, o escore traz o gosto, e o conteúdo, no cenário 1, amplia o catálogo sem mudar as métricas principais.")


def cenario1(p):
    s = novo_slide(p, "Resultado: usuário antigo", "No teste, empata com o óbvio na conversão e é o único que acerta o gosto")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Conversão@10 e AUC de gosto no teste, com IC de 95%", "Em números"], proporcao=0.66)
    imagem(s, FIGURAS / "40_cenario1.png", x1, y1, w1, h1)
    destaque(s, x2, y2 + 0.05, w2, "0,0520", "conversão@10 do modelo (5.663 usuários)", tamanho=30)
    destaque(s, x2, y2 + 1.4, w2, "0,5542", "AUC de gosto; popularidade + local fica em 0,4516, abaixo do acaso", cor=SALVIA, tamanho=30)
    destaque(s, x2, y2 + 2.75, w2, "+25%", "de conversão nos vizinhos por item + modelo, também abaixo do acaso no gosto", cor=MOSTARDA, tamanho=30)
    notas(s, "No teste, o modelo converte 0,052, em empate com a lista óbvia de popularidade e proximidade, mas é o único que fica acima do acaso no gosto. "
             "As técnicas colaborativas, que usamos como referência, convertem até 25% mais para usuários antigos, mas também ficam abaixo do acaso no gosto, e não atendem os cenários 2 e 3.")


def cenarios23(p):
    s = novo_slide(p, "Resultado: usuário novo e local novo", "Quase 5 vezes a popularidade global para quem nunca avaliou; o local novo é bem ordenado")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Usuário novo (6.783 usuários)", "Local novo (100 reais e 100 simulados)"])
    imagem(s, FIGURAS / "41_cenario2.png", x1, y1, w1, 2.6)
    texto(s, x1, y1 + 2.8, w1, 2.2, [
        [("Conversão@10 de 0,0452", {"negrito": True, "cor": TERRACOTA}), (" contra 0,0097 da popularidade global; AUC de gosto 0,5598.", {})],
        [("A cidade informada é o que mais ajuda; a categoria com peso baixo empata e amplia o catálogo.", {})],
        [("100% dos usuários recebem lista.", {})],
    ], tamanho=14, espaco=8, marcadores=True)
    imagem(s, FIGURAS / "42_cenario3.png", x2, y2, w2, 2.6)
    texto(s, x2, y2 + 2.8, w2, 2.2, [
        [("AUC de consumo 0,9209", {"negrito": True, "cor": TERRACOTA}), (" contra 0,9173 só com a localização: ", {}), ("empate", {"negrito": True}), (" nos locais reais; +0,0044 nos simulados.", {})],
        [("Cota de 1 local novo: listas que acertam um local novo vão de 21 para 126, com −0,0014 de conversão.", {})],
        [("O conteúdo pontua 100% dos locais novos; vizinhos e grafos, 0%.", {})],
    ], tamanho=14, espaco=8, marcadores=True)
    notas(s, "Para o usuário novo, o que mais ajuda é a cidade informada: a lista converte quase cinco vezes mais que a popularidade global. "
             "Para o local novo, o modelo põe quem de fato foi ao local bem acima dos demais (AUC de 0,92), mas o ganho do conteúdo sobre a localização, que aparecia na validação, não se confirmou nos locais reais do teste. Mesmo assim, só o conteúdo consegue pontuar um local sem avaliações.")


def demonstracao(p):
    item("i")
    s = novo_slide(p, "Demonstração", "O gosto de um usuário e o que o sistema recomenda")
    cartao(s, MARGEM, TOPO_CARTAO, 8.6, BASE_CARTAO - TOPO_CARTAO)
    imagem(s, RECORTES / "demo_perfil.png", MARGEM + 0.25, TOPO_CARTAO + 0.2, 8.1, 2.95)
    imagem(s, RECORTES / "demo_prateleira.png", MARGEM + 0.25, TOPO_CARTAO + 3.3, 8.1, 2.05)
    x = MARGEM + 8.9
    w = LARGURA - MARGEM - x
    cartao(s, x, TOPO_CARTAO, w, BASE_CARTAO - TOPO_CARTAO)
    texto(s, x + 0.3, TOPO_CARTAO + 0.25, w - 0.6, 0.45, "Roteiro ao vivo", tamanho=18, cor=SALVIA, fonte=FONTE_TITULO, negrito=True, espaco=0)
    passos = [("Demonstração", "Usuário #12.369: o gráfico do gosto, o mapa e as prateleiras"),
              ("Usuário novo", "Cheyenne + cafeteria: o que foi usado e a lista"),
              ("Local novo", "Um local real: usuários indicados e a decisão para um deles")]
    for i, (nome, descricao) in enumerate(passos):
        y = TOPO_CARTAO + 0.85 + i * 1.3
        circulo_numerado(s, x + 0.3, y, i + 1, [TERRACOTA, SALVIA, MOSTARDA][i], d=0.45)
        texto(s, x + 0.9, y, w - 1.15, 0.4, nome, tamanho=15, negrito=True, espaco=0)
        texto(s, x + 0.9, y + 0.4, w - 1.15, 0.9, descricao, tamanho=13, espaco=0)
    texto(s, x + 0.3, BASE_CARTAO - 0.6, w - 0.6, 0.4, "streamlit run app.py", tamanho=12, cor=SUAVE, fonte="Courier New", espaco=0)
    notas(s, "Demonstração ao vivo, cerca de 2 minutos e meio, com o app aberto antes da apresentação. "
             "1) Aba Demonstração, Usuário #12.369: o gráfico mostra o que pesa no gosto dele (restaurante americano e mesas ao ar livre de um lado; restaurante genérico e drive-thru do outro), as notas que ele deu e o mapa; embaixo, as prateleiras no estilo catálogo, cada cartão com a compatibilidade, a nota prevista e o porquê. "
             "2) Aba Usuário novo: Cheyenne + cafeteria + Wi-Fi; mostrar o que foi usado e as barras dos componentes. "
             "3) Aba Local novo: um local real; mostrar os usuários indicados e a posição dele na lista de um usuário. "
             "Se o app falhar, seguir pelas telas deste slide e do próximo.")


def telas(p):
    s = novo_slide(p, "A interface nos três cenários", "Cada lista mostra as barras dos componentes e o porquê de cada local")
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    itens = [("tela_antigo.png", "Usuário antigo", "Top 10 com explicação e nota prevista"),
             ("tela_novo.png", "Usuário novo", "Formulário opcional e regra de não esvaziar"),
             ("tela_local.png", "Local novo", "Usuários indicados e a decisão de recomendar")]
    for i, (arquivo, nome, descricao) in enumerate(itens):
        x = MARGEM + i * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO)
        circulo_numerado(s, x + 0.25, TOPO_CARTAO + 0.25, i + 1, [TERRACOTA, SALVIA, MOSTARDA][i], d=0.45)
        texto(s, x + 0.85, TOPO_CARTAO + 0.28, largura - 1.0, 0.4, nome, tamanho=16, negrito=True, fonte=FONTE_TITULO, espaco=0)
        imagem(s, RECORTES / arquivo, x + 0.15, TOPO_CARTAO + 0.85, largura - 0.3, 4.0)
        texto(s, x + 0.25, BASE_CARTAO - 0.75, largura - 0.5, 0.55, descricao, tamanho=13, cor=SUAVE, espaco=0)
    notas(s, "As três abas dos cenários. No usuário antigo, cada local tem as barras de conteúdo, escore, localização e popularidade e a explicação. No usuário novo, todos os campos são opcionais, e a lista nunca fica vazia. No local novo, os usuários indicados e a posição do local na lista de uma pessoa. As telas inteiras estão no apêndice.")


def conclusoes(p):
    item("Conclusões")
    s = novo_slide(p, "Conclusões", "Uma técnica atende os três cenários, com sinal de gosto vindo da qualidade do local")
    largura = (LARGURA - 2 * MARGEM - 0.6) / 3
    blocos = [
        ("O que funcionou", TERRACOTA, ["Uma técnica para os três cenários, com 100% de cobertura de usuários e de locais novos",
                                        "Entre as listas que convertem, é a que melhor acerta o gosto",
                                        "Localização e popularidade trazem a conversão; o escore, o gosto"]),
        ("Limitações", SALVIA, ["Conversão offline: local não avaliado pode só não ter sido visitado",
                                "Pouca personalização (correlação de rankings de 0,07)",
                                "Teste na pandemia; metadados de 2021",
                                "Ganho do conteúdo nos locais novos reais não confirmado"]),
        ("Próximos passos", MOSTARDA, ["Híbrido com vizinhos por item para usuários antigos",
                                       "Texto das avaliações no perfil",
                                       "Teste online com pessoas reais"]),
    ]
    for i, (titulo, cor, itens) in enumerate(blocos):
        x = MARGEM + i * (largura + 0.3)
        cartao(s, x, TOPO_CARTAO, largura, BASE_CARTAO - TOPO_CARTAO)
        texto(s, x + 0.3, TOPO_CARTAO + 0.25, largura - 0.6, 0.5, titulo, tamanho=19, cor=cor, fonte=FONTE_TITULO, negrito=True, espaco=0)
        texto(s, x + 0.3, TOPO_CARTAO + 0.95, largura - 0.6, BASE_CARTAO - TOPO_CARTAO - 1.2, itens, tamanho=17, espaco=16, marcadores=True)
    notas(s, "Em resumo: a técnica de conteúdo e escores de produto atende os três cenários do enunciado e é a que melhor acerta o gosto entre as listas que convertem. "
             "As limitações são honestas: a medida offline é uma aproximação, a personalização é pequena, o teste caiu na pandemia, e o ganho do conteúdo nos locais novos reais não se confirmou. Obrigado; ficamos abertos às perguntas.")


# ---------------------------------------------------------------- Apêndice
def apendice(p):
    item("Apêndice")
    divisoria(p, "Apêndice", "Detalhes para as perguntas")

    s = novo_slide(p, "A1. Sazonalidade e pandemia", "Julho tem 2 vezes o movimento de fevereiro; a pandemia corta a série em 2020")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Avaliações e nota média por ano", "Avaliações por mês do ano (2017 a 2019)"])
    imagem(s, FIGURAS / "17_avaliacoes_por_ano.png", x1, y1, w1, h1)
    imagem(s, FIGURAS / "18_avaliacoes_por_mes.png", x2, y2, w2, h2)
    notas(s, "Julho tem 2,05 vezes o movimento de fevereiro (3,29 vezes nas cidades turísticas), por isso a validação cobre um ano inteiro. As avaliações caem de 9.357 em fevereiro de 2020 para 906 em abril, e a coleta rareia em 2021.")

    s = novo_slide(p, "A2. Escolhas dos cenários 2 e 3 na validação", "A categoria declarada entra com peso baixo; o perfil do local novo é centrado em 3")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Usuário novo", "Local novo"])
    texto(s, x1, y1, w1, h1, [
        "Cidade + escore + popularidade: conversão 0,0484, quase 4 vezes a popularidade global (0,0129).",
        "Categorias com peso 0,05: empate nas duas métricas, catálogo de 27,9% para 31,8%.",
        "Categorias como filtro: conversão cai para 0,0239 — só 18,8% do que a pessoa avalia depois tem a categoria declarada.",
        "Pesos congelados: 0,05 / 0,19 / 0,475 / 0,285.",
    ], tamanho=15, espaco=12, marcadores=True)
    texto(s, x2, y2, w2, h2, [
        "Perfil centrado na média do usuário: o conteúdo quase não ordenava os locais novos (AUC de consumo de 0,51 sozinho).",
        "Centrado em 3 (o tipo de lugar que a pessoa frequenta): α = 0,5 soma 0,0119 de AUC de consumo ao só localização.",
        "Cota de 1 local novo: listas com local novo convertido de 29 para 149, mantendo 96% da conversão.",
    ], tamanho=15, espaco=12, marcadores=True)
    notas(s, "Detalhes da validação dos cenários 2 e 3, caso perguntem como os pesos foram escolhidos.")

    s = novo_slide(p, "A3. Curvas ROC e previsão de nota", "O escore + viés tem o menor erro; a conversão cai à metade depois do 1º ano do teste")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Curvas ROC no teste", "Previsão de nota e estabilidade"], proporcao=0.62)
    imagem(s, FIGURAS / "43_curvas_roc.png", x1, y1, w1, h1)
    texto(s, x2, y2, w2, h2, [
        [("RMSE: ", {"negrito": True}), ("1,0248 com escore + viés, contra 1,0842 do escore e 1,1337 da média global (21.121 avaliações).", {})],
        [("MAE: ", {"negrito": True}), ("0,7751.", {})],
        [("Estabilidade: ", {"negrito": True}), ("conversão de 0,0504 no 1º ano do teste e 0,0235 depois, em todas as ordenações.", {})],
        [("Validação × teste: ", {"negrito": True}), ("conversão do cenário 1 de 0,0739 para 0,0520; a queda atinge todos os métodos.", {})],
    ], tamanho=14, espaco=10, marcadores=True)
    notas(s, "A curva de gosto tem degraus porque a maioria dos usuários tem um ou dois locais bons e ruins no teste. A previsão de nota erra cerca de 1 ponto, o que confirma o pouco espaço para personalizar a nota; por isso o modelo ordena, e a nota prevista entra na interface só como informação.")

    for figura, titulo, mensagem in [
        ("inteira_antigo.png", "A4. Tela: usuário antigo", "Perfil, histórico e o top 10 com as barras dos componentes"),
        ("inteira_novo.png", "A5. Tela: usuário novo", "Formulário opcional, o que foi usado e a lista"),
        ("inteira_local.png", "A6. Tela: local novo", "Usuários indicados e a decisão de recomendar"),
    ]:
        s = novo_slide(p, titulo, mensagem)
        x, y, w, h = cartao_cheio(s)
        imagem(s, RECORTES / figura, x, y, w, h)
        notas(s, "Tela inteira da aba, gerada por scripts/capturar_telas.py.")


def main():
    preparar_recortes()
    p = Presentation()
    p.slide_width, p.slide_height = Inches(LARGURA), Inches(ALTURA)
    for montar in (capa, roteiro, sistema, base, historico, categorias, tecnica, ideia, passo_vetor, passo_perfil, passo_cosseno, passo_escores, passo_soma, passo_cenarios, tratamento, divisao, modelo_estimado, pesos, metricas, cenario1, cenarios23, demonstracao, telas, conclusoes, apendice):
        montar(p)
    SAIDA.mkdir(exist_ok=True)
    p.save(ARQUIVO)
    print(f"{ARQUIVO.relative_to(RAIZ)}: {len(p.slides)} slides")


if __name__ == "__main__":
    main()
