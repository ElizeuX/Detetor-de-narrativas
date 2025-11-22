#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DETECTOR DE ALITERAÇÕES E ASSONÂNCIAS PARA PDF

FUNCIONALIDADES:
- Lê PDF
- Extrai texto bruto
- Divide em frases (spaCy)
- Detecta:
    * ALITERAÇÃO  = repetição do fonema inicial
    * ASSONÂNCIA  = repetição de vogais tônicas ou vogais principais
- Lista SOMENTE frases que contenham pelo menos um dos fenômenos
- Gera relatório textual

USO:
    python detectar_som_pdf.py capitulo.pdf
"""

import sys
import re
import spacy
from phonemizer import phonemize
from pdfminer.high_level import extract_text

nlp = spacy.load("pt_core_news_sm")

# --------------------------------------------------------
# UTILITÁRIOS
# --------------------------------------------------------

def extrair_pdf(caminho):
    """Extrai texto bruto de PDF."""
    try:
        return extract_text(caminho)
    except Exception as e:
        print("Erro ao ler PDF:", e)
        sys.exit(1)


def fonemas_palavra(palavra: str) -> list:
    """Retorna lista de fonemas de uma palavra."""
    try:
        f = phonemize(palavra, language="pt-br")
    except:
        return []
    f = f.strip()
    if not f:
        return []
    return f.split()


def primeiro_fonema(palavra: str) -> str:
    """Primeiro fonema útil para aliteração."""
    f = fonemas_palavra(palavra)
    return f[0] if f else ""


def vogal_principal(palavra: str) -> str:
    """Extrai vogal principal para assonância (aproximação simples)."""
    # pega vogais fortes presentes na palavra
    vogais = re.findall(r"[aeiouáéíóúâêîôûãõ]", palavra.lower())
    return vogais[0] if vogais else ""


# --------------------------------------------------------
# DETECÇÃO
# --------------------------------------------------------

def detectar_aliteracao(frase: str):
    palavras = [w for w in frase.split() if any(c.isalpha() for c in w)]
    if len(palavras) < 2:
        return []

    fon = [primeiro_fonema(p.lower()) for p in palavras]
    grupos = []
    atual = [palavras[0]]

    for i in range(1, len(palavras)):
        if fon[i] == fon[i - 1] and fon[i] != "":
            atual.append(palavras[i])
        else:
            if len(atual) > 1:
                grupos.append(atual)
            atual = [palavras[i]]

    if len(atual) > 1:
        grupos.append(atual)

    return grupos


def detectar_assonancia(frase: str):
    palavras = [w for w in frase.split() if any(c.isalpha() for c in w)]
    if len(palavras) < 2:
        return []

    vog = [vogal_principal(p) for p in palavras]
    grupos = []
    atual = [palavras[0]]

    for i in range(1, len(palavras)):
        if vog[i] == vog[i - 1] and vog[i] != "":
            atual.append(palavras[i])
        else:
            if len(atual) > 1:
                grupos.append(atual)
            atual = [palavras[i]]

    if len(atual) > 1:
        grupos.append(atual)

    return grupos


# --------------------------------------------------------
# ANÁLISE PRINCIPAL
# --------------------------------------------------------

def analisar_texto(texto: str):
    doc = nlp(texto)
    frases = [s.text.strip() for s in doc.sents if s.text.strip()]

    resultados = []

    for i, frase in enumerate(frases, start=1):
        alits = detectar_aliteracao(frase)
        assons = detectar_assonancia(frase)

        if alits or assons:   # <<< SOMENTE frases com fenômenos sonoros
            resultados.append({
                "num": i,
                "frase": frase,
                "alit": alits,
                "asson": assons
            })

    return resultados


# --------------------------------------------------------
# RELATÓRIO
# --------------------------------------------------------

def salvar_relatorio(analise):
    with open("relatorio_sonoro.txt", "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE ALITERAÇÕES E ASSONÂNCIAS\n")
        f.write("=======================================\n\n")

        if not analise:
            f.write("Nenhuma aliteração ou assonância encontrada.\n")
            return

        for item in analise:
            f.write(f"Frase {item['num']}:\n")
            f.write(f"{item['frase']}\n")

            if item["alit"]:
                f.write("  Aliterações:\n")
                for grupo in item["alit"]:
                    f.write(f"    - {' '.join(grupo)}\n")

            if item["asson"]:
                f.write("  Assonâncias:\n")
                for grupo in item["asson"]:
                    f.write(f"    - {' '.join(grupo)}\n")

            f.write("\n")

    print("Relatório gerado: relatorio_sonoro.txt")


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: python detectar_som_pdf.py arquivo.pdf")
        sys.exit(1)

    pdf = sys.argv[1]

    print("Lendo PDF…")
    texto = extrair_pdf(pdf)

    print("Analisando som…")
    analise = analisar_texto(texto)

    print("Gerando relatório…")
    salvar_relatorio(analise)

    print("Concluído.")


if __name__ == "__main__":
    main()
