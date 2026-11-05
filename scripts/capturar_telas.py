"""Salva as telas da interface em figuras/50_ a 53_, com casos fixos.

Requer o app rodando (`streamlit run app.py`, porta 8501) e o Playwright com o Chromium:

    python scripts/capturar_telas.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ENDERECO = "http://localhost:8501"
PASTA = Path(__file__).resolve().parent.parent / "figuras"
USUARIO_DEMONSTRACAO = "12369"
USUARIO_ANTIGO = "70927"


def esperar(pagina, segundos=3):
    """Espera o Streamlit terminar de rodar o script."""
    pagina.wait_for_timeout(500)
    pagina.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120_000)
    pagina.wait_for_timeout(segundos * 1000)


def aba(pagina, nome):
    pagina.get_by_role("tab", name=nome).click()
    pagina.wait_for_timeout(800)


def digitar(pagina, rotulo, texto, indice=0):
    campo = pagina.get_by_label(rotulo).nth(indice)
    campo.fill(texto)
    campo.press("Enter")
    esperar(pagina)


def escolher(pagina, rotulo, opcoes, indice=0):
    """Seleciona opções de um selectbox ou multiselect digitando e confirmando com Enter."""
    caixa = pagina.get_by_label(rotulo).nth(indice)
    for opcao in opcoes:
        caixa.click()
        caixa.fill(opcao)
        pagina.keyboard.press("Enter")
        pagina.wait_for_timeout(400)
    pagina.keyboard.press("Escape")


def salvar(pagina, nome, altura):
    pagina.set_viewport_size({"width": 1800, "height": altura})
    pagina.wait_for_timeout(1500)
    pagina.screenshot(path=PASTA / nome)
    print(f"figuras/{nome}")


with sync_playwright() as playwright:
    navegador = playwright.chromium.launch()
    pagina = navegador.new_page(viewport={"width": 1400, "height": 900}, color_scheme="light")
    pagina.goto(ENDERECO)
    pagina.get_by_role("tab", name="Demonstração").wait_for(timeout=180_000)
    esperar(pagina)

    digitar(pagina, "Número do usuário", USUARIO_DEMONSTRACAO, indice=0)
    salvar(pagina, "50_demonstracao.png", 3000)

    pagina.set_viewport_size({"width": 1400, "height": 900})
    aba(pagina, "Usuário antigo")
    digitar(pagina, "Número do usuário", USUARIO_ANTIGO, indice=1)
    salvar(pagina, "51_usuario_antigo.png", 1250)

    pagina.set_viewport_size({"width": 1400, "height": 900})
    aba(pagina, "Usuário novo")
    escolher(pagina, "Cidade", ["Cheyenne"], indice=0)
    escolher(pagina, "Categorias de que gosta", ["Cafeteria"])
    escolher(pagina, "Atributos desejados", ["Wi-Fi"])
    pagina.get_by_role("button", name="Recomendar").click()
    esperar(pagina)
    salvar(pagina, "52_usuario_novo.png", 1300)

    pagina.set_viewport_size({"width": 1400, "height": 900})
    aba(pagina, "Local novo")
    salvar(pagina, "53_local_novo.png", 1350)
    navegador.close()
