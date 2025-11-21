#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANÁLISE MORFOSSINTÁTICA – PDF
==============================

• Lê PDF
• Extrai texto
• Conta:
    - substantivos
    - adjetivos
    - verbos
• Calcula métricas:
    - N/V (substantivos ÷ verbos)
    - ADJ/N (adjetivos ÷ substantivos)
    - Densidade verbal (verbos ÷ total)
    - Adjetivos por 1000 palavras
• Gera relatório .txt com alertas e tabela comparativa

Requisitos:
    pip install pdfminer.six spacy
    python -m spacy download pt_core_news_sm
"""

import spacy
from pdfminer.high_level import extract_text
from collections import Counter
import re

# Carregar spaCy
nlp = spacy.load("pt_core_news_sm")

# -------------------------------------------------------------

def extrair_pdf(caminho_pdf: str) -> str:
    """Extrai texto bruto do PDF."""
    try:
        return extract_text(caminho_pdf)
    except Exception as e:
        print("Erro ao ler PDF:", e)
        return ""

# -------------------------------------------------------------

def analisar_classes(texto: str):
    """Conta substantivos, adjetivos, verbos e calcula métricas."""

    doc = nlp(texto)

    total_tokens = 0
    substantivos = 0
    adjetivos = 0
    verbos = 0

    for token in doc:
        if token.is_alpha:
            total_tokens += 1

            if token.pos_ in ("NOUN", "PROPN"):
                substantivos += 1
            elif token.pos_ == "ADJ":
                adjetivos += 1
            elif token.pos_ == "VERB":
                verbos += 1

    # Métricas
    n_v = substantivos / verbos if verbos else 0
    adj_n = adjetivos / substantivos if substantivos else 0
    dens_verbos = verbos / total_tokens if total_tokens else 0
    adj_1000 = (adjetivos / total_tokens) * 1000 if total_tokens else 0

    return {
        "tokens": total_tokens,
        "substantivos": substantivos,
        "adjetivos": adjetivos,
        "verbos": verbos,
        "n_v": n_v,
        "adj_n": adj_n,
        "densidade_verbos": dens_verbos,
        "adj_por_1000": adj_1000
    }

# -------------------------------------------------------------

def gerar_alertas(stats):
    avisos = []

    # N/V
    if stats["n_v"] < 0.8:
        avisos.append("N/V baixo demais: narrativa acelerada, muito verbal.")
    elif stats["n_v"] > 1.8:
        avisos.append("N/V alto: excesso de substantivos. Texto pode estar descritivo demais.")

    # ADJ/N
    if stats["adj_n"] > 0.22:
        avisos.append("ADJ/N elevado: adjetivação pesada, risco de rococó.")
    elif stats["adj_n"] < 0.06:
        avisos.append("ADJ/N muito baixo: estilo seco ou minimalista.")

    # densidade verbal
    if stats["densidade_verbos"] < 0.10:
        avisos.append("Poucos verbos: narrativa lenta e contemplativa.")
    elif stats["densidade_verbos"] > 0.22:
        avisos.append("Muitos verbos: narrativa frenética ou apressada.")

    # adjetivos por 1000
    if stats["adj_por_1000"] > 120:
        avisos.append("Adjetivos/1000 muito alto: prosa excessivamente florida.")
    elif stats["adj_por_1000"] < 50:
        avisos.append("Adjetivos/1000 muito baixo: prosa seca para deserto do Saara.")

    if not avisos:
        avisos.append("Distribuição linguística equilibrada. Nada crítico detectado.")

    return avisos

# -------------------------------------------------------------

def tabela_referencia():
    return """
TABELA DE REFERÊNCIA
=====================

N/V – Substantivos ÷ Verbos
  0.8–1.2  → ritmo equilibrado
  1.3–1.8  → literário/descritivo
  > 1.8    → estático

ADJ/N – Adjetivos ÷ Substantivos
  0.05–0.08 → econômico
  0.08–0.14 → equilibrado
  0.15–0.22 → lírico
  > 0.22    → rococó

Densidade verbal (% verbos)
  12–18%  → ficção comum
  18–25%  → ação/policial
  < 10%   → contemplação

Adjetivos por 1000 palavras
  50–90   → normal
  90–120  → lírico
  > 120   → exagerado
"""

# -------------------------------------------------------------

def salvar_relatorio(stats, avisos, caminho):
    with open(caminho, "w", encoding="utf-8") as f:

        # Cabeçalho
        f.write("# 🧠 Análise Morfossintática – Relatório\n\n")

        # ---------------------------------------
        # CONTAGEM
        # ---------------------------------------
        f.write("## 📦 Contagem Geral\n")
        f.write("| Categoria | Valor |\n")
        f.write("|-----------|-------|\n")
        f.write(f"| Palavras consideradas | {stats['tokens']} |\n")
        f.write(f"| Substantivos | {stats['substantivos']} |\n")
        f.write(f"| Adjetivos | {stats['adjetivos']} |\n")
        f.write(f"| Verbos | {stats['verbos']} |\n\n")

        # ---------------------------------------
        # MÉTRICAS
        # ---------------------------------------
        f.write("## 📊 Métricas\n")
        f.write("| Métrica | Valor |\n")
        f.write("|---------|-------|\n")
        f.write(f"| **N/V** (substantivos ÷ verbos) | {stats['n_v']:.3f} |\n")
        f.write(f"| **ADJ/N** (adjetivos ÷ substantivos) | {stats['adj_n']:.3f} |\n")
        f.write(f"| **Densidade verbal** | {stats['densidade_verbos']*100:.2f}% |\n")
        f.write(f"| **Adjetivos por 1000 palavras** | {stats['adj_por_1000']:.1f} |\n\n")

        # ---------------------------------------
        # ALERTAS
        # ---------------------------------------
        f.write("## ⚠️ Alertas\n")
        if avisos:
            for a in avisos:
                f.write(f"- {a}\n")
        else:
            f.write("- Nenhum alerta detectado.\n")
        f.write("\n")

        # ---------------------------------------
        # TABELA DE REFERÊNCIA
        # ---------------------------------------
        f.write("## 📚 Tabela de Referência\n")
        f.write("```\n")
        f.write(tabela_referencia())
        f.write("```\n")


# -------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Análise de classes gramaticais em PDF")
    parser.add_argument("pdf", help="PDF de entrada")
    parser.add_argument("saida", help="Arquivo .txt de relatório")
    args = parser.parse_args()

    print("Lendo PDF…")
    texto = extrair_pdf(args.pdf)

    print("Analisando…")
    stats = analisar_classes(texto)

    print("Gerando alertas…")
    avisos = gerar_alertas(stats)

    print("Gerando relatório…")
    salvar_relatorio(stats, avisos, args.saida)

    print("Pronto.")
    print(f"Relatório salvo em: {args.saida}")

# -------------------------------------------------------------

if __name__ == "__main__":
    main()
