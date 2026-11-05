"""Gera a apresentação do Trabalho T1 em `apresentacao/T1_Sistema_Recomendacao.pptx`.

O visual segue o modelo da usuária no Canva (fundo bege, títulos em terracota, cartões brancos).
As fontes do modelo (Montserrat e Inter) não estão instaladas, então os títulos usam Century Gothic
e o texto, Arial; no Canva, volta-se às originais. Os números vêm do `relatório.md`.

    python scripts/gerar_ppt.py
"""

from pathlib import Path

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
def novo_slide(apresentacao, titulo, mensagem=None):
    """Layout de conteúdo: título em terracota e, abaixo, a mensagem do slide em sálvia."""
    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    _fundo(slide)
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


def sistema(p):
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


def conteudo(p):
    s = novo_slide(p, "Conteúdo", "Cada local vira um vetor; cada usuário, um perfil")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Do local ao perfil", "Os 5 vizinhos por cosseno de três locais"], proporcao=0.45)
    texto(s, x1, y1, w1, h1, [
        [("Vetor do local: ", {"negrito": True}), ("TF-IDF das categorias e dos atributos declaráveis (entrega, acessibilidade, pagamento…), normalizado em L2.", {})],
        [("Similaridade: ", {"negrito": True}), ("cosseno, levado para 0 a 1: sim = (cos + 1) / 2.", {})],
        [("Perfil do usuário: ", {"negrito": True}), ("soma dos vetores dos locais avaliados, com peso pela nota.", {})],
        [("p", {"negrito": True, "cor": TERRACOTA}), ("u", {"negrito": True, "cor": TERRACOTA, "tamanho": 11}), (" ∝ Σ (nota − c", {"negrito": True, "cor": TERRACOTA}), ("u", {"negrito": True, "cor": TERRACOTA, "tamanho": 11}), (") · x", {"negrito": True, "cor": TERRACOTA}), ("i", {"negrito": True, "cor": TERRACOTA, "tamanho": 11})],
        [("c", {"negrito": True}), ("u", {"negrito": True, "tamanho": 11}), (" é a média do usuário no cenário 1 (do que ele gosta mais) e 3 no cenário 3 (o tipo de lugar que frequenta).", {})],
    ], tamanho=16, espaco=12, marcadores=True)
    imagem(s, FIGURAS / "20_vizinhos_conteudo.png", x2, y2, w2, h2)
    notas(s, "O conteúdo usa só o que um local recém-cadastrado poderia informar: categorias e atributos declaráveis. O TF-IDF dá menos peso aos atributos que quase todos têm. "
             "O perfil soma os vetores dos locais avaliados, positivos quando a nota passa do centro e negativos abaixo. À direita, os vizinhos de uma pizzaria, um café e um bar são do mesmo tipo: o cosseno mede o tipo de lugar, não a qualidade. Por isso entram os escores.")


def escores(p):
    s = novo_slide(p, "Escores e pontuação", "Qualidade, popularidade e localização completam o conteúdo")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Escore bayesiano", "Os componentes e os pesos de cada cenário"], proporcao=0.45)
    figura_com_legenda(s, FIGURAS / "30_escore_bayesiano.png", (x1, y1, w1, h1), "escore = (v·R + m·C) / (v + m), com m no percentil 25 das avaliações por local", tamanho=13)
    texto(s, x2, y2, w2, 1.6, [
        [("Popularidade: ", {"negrito": True}), ("log(1 + v) / log(1 + máx v)", {})],
        [("Localização: ", {"negrito": True}), ("média de exp(−km / 200) até os locais que a pessoa avaliou", {})],
        [("Nota prevista: ", {"negrito": True}), ("escore do local + viés do usuário", {})],
    ], tamanho=15, espaco=8, marcadores=True)
    linhas = [("Cenário", "Conteúdo", "Escore", "Localização", "Popularidade"),
              ("1. Usuário antigo", "0,1", "0,2", "0,5", "0,2"),
              ("2. Usuário novo", "0,05", "0,19", "0,475", "0,285"),
              ("3. Local novo", "0,5", "—", "0,5", "—")]
    tabela = s.shapes.add_table(4, 5, Inches(x2), Inches(y2 + 1.75), Inches(w2), Inches(1.9)).table
    tabela.columns[0].width = Inches(w2 * 0.24)
    for j in range(1, 5):
        tabela.columns[j].width = Inches(w2 * 0.19)
    for i, linha in enumerate(linhas):
        for j, valor in enumerate(linha):
            celula = tabela.cell(i, j)
            celula.fill.solid()
            celula.fill.fore_color.rgb = TERRACOTA if i == 0 else (TINTA_CARTAO if i % 2 == 0 else BRANCO)
            celula.text_frame.text = valor
            celula.margin_left = celula.margin_right = Inches(0.05)
            paragrafo = celula.text_frame.paragraphs[0]
            paragrafo.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            fonte = paragrafo.runs[0].font
            fonte.name, fonte.size, fonte.bold = FONTE_TEXTO, Pt(12), i == 0
            fonte.color.rgb = BRANCO if i == 0 else TEXTO
            celula.vertical_anchor = MSO_ANCHOR.MIDDLE
    texto(s, x2, y2 + 3.85, w2, 1.0, [
        "Usuário novo: o que ele declara faz o papel do histórico.",
        "Cenário 3: a lista do usuário antigo reserva 1 posição a um local novo (cota).",
    ], tamanho=13, cor=SUAVE, espaco=4)
    notas(s, "O escore bayesiano evita que um local com duas notas 5 passe à frente de um com centenas de avaliações. A popularidade usa o logaritmo para não ser dominada pelos maiores, e a localização decai com a distância, com τ de 200 km. "
             "Os pesos de cada cenário foram escolhidos na validação, como mostramos adiante. No cenário 3, o local novo não tem escore nem popularidade, então só conteúdo e localização pontuam.")


def tratamento(p):
    s = novo_slide(p, "Tratamento dos dados", "Do arquivo bruto à base limpa, e o que entra no vetor de conteúdo")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["Funil", "O vetor de conteúdo"], proporcao=0.55)
    etapas = [("12.088", "linhas de locais", 1.0, TEXTO), ("12.016", "sem 72 cópias", 0.99, TEXTO), ("11.931", "com categoria", 0.98, TEXTO), ("1.863", "no recorte de alimentação (8 incluídos à mão)", 0.42, TERRACOTA),
              ("433.918", "avaliações desses locais", 1.0, TEXTO), ("429.622", "sem 4.296 duplicatas exatas", 0.97, TERRACOTA)]
    for i, (valor, rotulo, fracao, cor) in enumerate(etapas):
        y = y1 + i * 0.56 + (0.2 if i >= 4 else 0)
        barra = cartao(s, x1, y, max(0.5, (w1 - 0.1) * 0.42 * fracao), 0.44, cor=TINTA_CARTAO if cor == TEXTO else RGBColor(0xF3, 0xDF, 0xD3))
        texto(s, x1 + 0.15, y, 1.4, 0.44, valor, tamanho=16, negrito=True, cor=cor, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
        texto(s, x1 + (w1 - 0.1) * 0.42 + 0.2, y, w1 * 0.58 - 0.2, 0.44, rotulo, tamanho=14, ancora=MSO_ANCHOR.MIDDLE, espaco=0)
    texto(s, x1, y1 + h1 - 0.55, w1, 0.6, "Mantidos, com justificativa: avaliações sem texto (41%) e rajadas (1,4%). Os 238 locais fechados ficam na base, mas não são recomendados.", tamanho=13, cor=SUAVE, espaco=0)
    texto(s, x2, y2, w2, h2, [
        [("Entra: ", {"negrito": True, "cor": SALVIA}), ("categorias e atributos declaráveis (serviço, acessibilidade, comodidades, pagamento, planejamento)", {})],
        [("Fica fora: ", {"negrito": True, "cor": TERRACOTA}), ("atributos que vêm do comportamento dos clientes (\"popular para\", público, ambiente) e os da pandemia", {})],
        [("Fica fora: ", {"negrito": True, "cor": TERRACOTA}), ("preço, que falta em 90% dos locais sem avaliação e em 5% dos populares", {})],
        [("Fica fora: ", {"negrito": True, "cor": TERRACOTA}), ("texto das avaliações, que um local novo não tem", {})],
        [("Resultado: ", {"negrito": True}), ("167 tokens (136 de categorias e 31 de atributos)", {})],
    ], tamanho=15, espaco=12, marcadores=True)
    notas(s, "O recorte usa a categoria principal: um hotel com restaurante fica de fora. Removemos cópias, locais sem categoria e duplicatas exatas de avaliações. "
             "No vetor, a regra é só usar o que um local recém-cadastrado poderia informar; atributos derivados do comportamento dos clientes e o preço carregam viés de popularidade.")


def divisao(p):
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
    s = novo_slide(p, "Métricas", "Duas perguntas, duas métricas: a pessoa foi? E gostou?")
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


def pesos(p):
    s = novo_slide(p, "Estimação", "Os pesos trocam 3,6% de conversão por mais gosto; o escore é quem acerta o gosto")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = dois_cartoes(s, ["286 combinações de pesos na validação", "Ablação: tirar ou usar só um componente"], proporcao=0.47)
    imagem(s, FIGURAS / "31_grade_pesos.png", x1, y1, w1, h1 - 0.9)
    texto(s, x1, y1 + h1 - 0.8, w1, 0.8, [[("Critério: ", {"negrito": True}), ("conversão ≥ 95% da melhor; entre essas, a maior AUC de gosto. Escolhido: 0,1 / 0,2 / 0,5 / 0,2 (conversão 0,0739; gosto 0,5850).", {})]], tamanho=13, espaco=0)
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
    for montar in (capa, sistema, base, historico, categorias, tecnica, conteudo, escores, tratamento, divisao, metricas, pesos, cenario1, cenarios23, demonstracao, telas, conclusoes, apendice):
        montar(p)
    SAIDA.mkdir(exist_ok=True)
    p.save(ARQUIVO)
    print(f"{ARQUIVO.relative_to(RAIZ)}: {len(p.slides)} slides")


if __name__ == "__main__":
    main()
