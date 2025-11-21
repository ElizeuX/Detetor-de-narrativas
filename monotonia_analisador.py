#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANALISADOR DE MONOTONIA PARA PDF
================================

FUNCIONALIDADES
---------------
- Lê PDF (capítulo único).
- Extrai texto puro.
- Divide em parágrafos.
- Para cada parágrafo:
    * calcula tamanho das frases
    * índice de ritmo (IR)
    * alternância (SW)
    * classifica monotonia
- Gera:
    1. relatorio_monotonia.txt
    2. texto_marcado.txt

USO:
    python monotonia_analisador_pdf.py capitulo.pdf
"""

import sys
import re
import statistics
import spacy
from pdfminer.high_level import extract_text

# Carregar modelo spaCy PT-BR
nlp = spacy.load("pt_core_news_sm")

# -------------------------------------------------------
# Extração e limpeza
# -------------------------------------------------------

def extrair_pdf(caminho):
    """Extrai texto bruto do PDF."""
    try:
        return extract_text(caminho)
    except Exception as e:
        print("Erro ao ler PDF:", e)
        sys.exit(1)


def limpar_texto(texto):
    """Mantém quebras de parágrafo e limpa espaços."""
    texto = texto.replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


# -------------------------------------------------------
# Monotonia
# -------------------------------------------------------

def medir_monotonia(paragrafo: str):
    """Analisa ritmo e alternância de frases em um parágrafo."""
    doc = nlp(paragrafo)
    tamanhos = [len(s.text.split()) for s in doc.sents]

    if not tamanhos:
        return {"frases": [], "ir": 0, "sw": 0, "nivel": "Indeterminado"}

    media = statistics.mean(tamanhos)
    desvio = statistics.pstdev(tamanhos)
    ir = desvio / media if media else 0

    # Categorias: C, M, L
    def cat(n):
        if n < 10:
            return "C"
        elif n <= 20:
            return "M"
        return "L"

    categorias = [cat(n) for n in tamanhos]
    sw = sum(1 for i in range(1, len(categorias)) if categorias[i] != categorias[i - 1])

    # Classificação
    if ir < 0.15 and sw <= 1:
        nivel = "Monótono"
    elif ir < 0.30:
        nivel = "Ritmo moderado"
    elif ir < 0.55:
        nivel = "Variado"
    else:
        nivel = "Irregular"

    return {"frases": tamanhos, "ir": ir, "sw": sw, "nivel": nivel}


def analisar_texto(texto):
    """Divide em parágrafos e analisa um por um."""
    paragrafos = [p.strip() for p in texto.split("\n") if p.strip()]
    resultados = []

    for i, p in enumerate(paragrafos, start=1):
        dados = medir_monotonia(p)
        resultados.append({
            "num": i,
            "texto": p,
            **dados
        })

    return resultados


# -------------------------------------------------------
# Relatórios
# -------------------------------------------------------

def salvar_relatorio(resultados):
    with open("relatorio_monotonia.txt", "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE MONOTONIA POR PARÁGRAFO\n")
        f.write("=====================================\n\n")

        for r in resultados:
            f.write(f"Parágrafo {r['num']}\n")
            f.write(f"Classificação: {r['nivel']}\n")
            f.write(f"Tamanhos das frases: {r['frases']}\n")
            f.write(f"IR (Índice de Ritmo): {r['ir']:.3f}\n")
            f.write(f"SW (Alternância): {r['sw']}\n")
            f.write("-" * 50 + "\n")


def salvar_marcado(resultados):
    """Cria texto original com marcação nos parágrafos monótonos."""
    linhas = []
    for r in resultados:
        if r["nivel"] == "Monótono":
            linhas.append(f"[MONOTONO] {r['texto']}")
        else:
            linhas.append(r["texto"])

    with open("texto_marcado.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(linhas))


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: python monotonia_analisador_pdf.py capitulo.pdf")
        sys.exit(1)

    pdf = sys.argv[1]

    print("Lendo PDF...")
    texto = extrair_pdf(pdf)

    print("Limpando texto...")
    texto = limpar_texto(texto)

    print("Analisando parágrafos...")
    resultados = analisar_texto(texto)

    print("Gerando relatórios...")
    salvar_relatorio(resultados)
    salvar_marcado(resultados)

    print("\nPronto.")
    print("Arquivos gerados:")
    print("  relatorio_monotonia.txt")
    print("  texto_marcado.txt")


if __name__ == "__main__":
    main()

