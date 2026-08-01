from groq import Groq
import feedparser
from datetime import datetime
import os

API_KEY = os.getenv("GROQ_API_KEY")
FONTES = [
    "https://g1.globo.com/rss/g1/",
    "https://feeds.bbci.co.uk/portuguese/rss.xml",
]

# Caminho completo do arquivo HTML (mais seguro)
PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_HTML = os.path.join(PASTA, "noticias.html")

# ======================
# 1. Buscar notícias
# ======================
def buscar_noticias(max_noticias=10):
    noticias = []
    for url in FONTES:
        feed = feedparser.parse(url)
        for entrada in feed.entries[:5]:
            titulo = entrada.get("title", "")
            link = entrada.get("link", "#")
            resumo = entrada.get("summary", entrada.get("description", ""))
            resumo = resumo.replace("<p>", "").replace("</p>", "").strip()
            if len(resumo) > 300:
                resumo = resumo[:300] + "..."
            noticias.append({
                "titulo": titulo,
                "link": link,
                "resumo": resumo,
                "fonte": feed.feed.get("title", "Fonte")
            })
    return noticias[:max_noticias]

# ======================
# 2. Pedir para a IA
# ======================
def gerar_boletim_com_ia(noticias):
    client = Groq(api_key=API_KEY)

    texto_noticias = ""
    for i, n in enumerate(noticias, 1):
        texto_noticias += f"{i}. Título: {n['titulo']}\n   Resumo: {n['resumo']}\n   Fonte: {n['fonte']}\n   Link: {n['link']}\n\n"

    prompt = f"""
Você é o editor de um site de notícias brasileiro.
Abaixo estão notícias reais coletadas agora.

Sua tarefa:
- Escolha as 6 a 8 mais importantes
- Melhore os títulos se necessário
- Escreva um resumo objetivo de 3 a 4 frases
- Classifique em uma categoria (Política, Economia, Internacional, Tecnologia, Esporte, Saúde, etc.)
- Mantenha o link original
- Seja factual e neutro

Retorne APENAS no formato abaixo (sem texto extra):

CATEGORIA | TÍTULO | RESUMO | FONTE | LINK

Notícias coletadas:
{texto_noticias}
"""

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return resposta.choices[0].message.content

# ======================
# 3. Gerar o HTML
# ======================
def gerar_html(boletim_ia):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    cards = ""
    linhas_validas = 0

    for linha in boletim_ia.strip().split("\n"):
        if "|" not in linha:
            continue
        partes = [p.strip() for p in linha.split("|")]
        if len(partes) < 5:
            continue

        categoria, titulo, resumo, fonte, link = partes[0], partes[1], partes[2], partes[3], partes[4]
        linhas_validas += 1

        cards += f"""
        <article class="noticia">
            <span class="categoria">{categoria}</span>
            <h3>{titulo}</h3>
            <p class="resumo">{resumo}</p>
            <div class="rodape-noticia">
                <span class="fonte">Fonte: {fonte}</span>
                <a href="{link}" class="link" target="_blank">Ler original</a>
            </div>
        </article>
        """

    if linhas_validas == 0:
        cards = "<p>Nenhuma notícia foi processada corretamente pela IA.</p>"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notícias IA</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>Notícias IA</h1>
            <p class="subtitle">Resumos inteligentes das principais notícias</p>
        </div>
    </header>

    <main class="container">
        <section class="boletim">
            <h2>Boletim de Hoje</h2>
            <p class="data">{data_hoje}</p>
        </section>

        <section class="noticias">
            {cards}
        </section>
    </main>

    <footer>
        <div class="container">
            <p>Site alimentado por Inteligência Artificial • Atualizado automaticamente</p>
        </div>
    </footer>
</body>
</html>
"""
    return html

# ======================
# EXECUÇÃO
# ======================
if __name__ == "__main__":
    print("Buscando notícias...")
    noticias = buscar_noticias()
    print(f"Encontradas {len(noticias)} notícias.")

    print("Enviando para a IA...")
    boletim = gerar_boletim_com_ia(noticias)

    print("\n--- Resposta da IA ---")
    print(boletim)
    print("----------------------\n")

    html_final = gerar_html(boletim)

    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"Arquivo salvo em: {ARQUIVO_HTML}")
    print("Abra o noticias.html no navegador.")