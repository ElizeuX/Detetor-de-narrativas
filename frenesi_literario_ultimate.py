#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FRENÊSI LITERÁRIO™ – Ultimate Edition
Análise estilística completa para textos extraídos de PDF.

Requer:
    pip install pdfminer.six spacy lexicalrichness
    python -m spacy download pt_core_news_sm
"""

import re
import statistics
from collections import Counter
from pdfminer.high_level import extract_text
from lexicalrichness import LexicalRichness
import spacy

nlp = spacy.load("pt_core_news_sm")

STOPWORDS = {
    "a","o","os","as","de","da","do","das","dos",
    "e","em","no","na","nos","nas","por","para",
    "um","uma","uns","umas",
    "que","se","com","como","ao","à","às","aos",
    "mas","ou","ser","estar"
}

from spacy.lang.pt.stop_words import STOP_WORDS

STOPWORDS = set(STOP_WORDS)

VERBOS_FRACOS = {
    # clássicos da preguiça existencial
    "ser", "estar", "ter", "haver",

    # ligação (ligam coisas, não movem nada)
    "ficar", "parecer", "continuar", "permanecer",
    "tornar-se", "manter-se", "virar",

    # auxiliares que carregam frase nas costas
    "poder", "dever", "precisar", "costumar",
    "saber" , "querer" , "deixar", "tentar",

    # genéricos que não dizem nada sozinhos
    "ir", "vir", "ver", "sentir", "notar",
    "olhar", "achar", "pensar", "dizer",
    "fazer", "passar", "estar", "voltar",

    # estado em vez de ação
    "existir", "acontecer", "ocorrer",

    # vazios em narrativa de ação
    "estar", "ficar", "seguir", "começar",

    # verbos que inflam o texto mas não movem a cena
    "parecer", "parecia", "estava", "tinha",

    # conversacionais demais
    "dizer", "falar", "contar",

    # comodins que resolvem tudo sem mostrar nada
    "ver", "sentir", "saber"
}


def extrair_texto_pdf(caminho_pdf):
    return extract_text(caminho_pdf)

def limpar(texto):
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def segmentar_frases(texto):
    doc = nlp(texto)
    return [sent.text for sent in doc.sents if sent.text.strip()]

def densidade_lexical(texto, janela=100):
    palavras = re.findall(r"\w+", texto.lower())
    blocos = [palavras[i:i+janela] for i in range(0, len(palavras), janela)]
    ttrs = [len(set(b)) / len(b) for b in blocos if len(b) == janela]
    return sum(ttrs) / len(ttrs) if ttrs else 0

def repeticao(texto):
    palavras = re.findall(r"\w+", texto.lower())
    return 1 - (len(set(palavras)) / len(palavras))

def examinar(texto):
    palavras = re.findall(r"\w+", texto.lower())
    frases = segmentar_frases(texto)

    # REMOVE STOPWORDS AQUI
    palavras_filtradas = [p for p in palavras if p not in STOPWORDS]

    tamanhos_frase = [len(f.split()) for f in frases]
    contador = Counter(palavras_filtradas)

    lex = LexicalRichness(texto)

    adverbios_mente = [p for p in palavras if p.endswith("mente")]
    verbos_fracos = [p for p in palavras if p in VERBOS_FRACOS]

    return {
        "total_palavras": len(palavras),
        "total_frases": len(frases),
        "tamanho_medio_frase": statistics.mean(tamanhos_frase),
        "tamanho_max_frase": max(tamanhos_frase),
        "tamanho_min_frase": min(tamanhos_frase),
        "top_20_palavras": contador.most_common(20),  # AGORA SEM ARTIGOS
        "adv_mente": len(adverbios_mente),
        "verbos_fracos": len(verbos_fracos),
        "ttr": lex.ttr,
        "mtld": lex.mtld(),
        "hdd": lex.hdd(),
        "densidade_lexical": densidade_lexical(texto),
        "indice_repeticao": repeticao(texto),
    }


def diagnostico(stats):
    avisos = []

    if stats["ttr"] < 0.18:
        avisos.append("Vocabulário repetitivo. Reforçar sinônimos.")
    elif stats["ttr"] > 0.45:
        avisos.append("Vocabulário muito alto. Cuidado para não soar pedante.")

    if stats["adv_mente"] > 25:
        avisos.append("Uso elevado de advérbios em -mente. Risco de prosa açucarada.")

    if stats["verbos_fracos"] > stats["total_palavras"] * 0.06:
        avisos.append("Alta incidência de verbos fracos. Narrativa pode estar passiva.")

    if stats["tamanho_medio_frase"] > 28:
        avisos.append("Frases muito longas. Risco de tontura no leitor.")
    elif stats["tamanho_medio_frase"] < 10:
        avisos.append("Frases curtas demais. Risco de estilo telegráfico.")

    if stats["indice_repeticao"] > 0.85:
        avisos.append("Repetição elevada. Texto pode estar circular.")

    return avisos or ["Estilisticamente saudável. Nenhum problema evidente."]

def salvar_relatorio(stats, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("FRENÊSI LITERÁRIO™ – Relatório Completo\n")
        f.write("=======================================\n\n")

        f.write("=== Métricas Gerais ===\n")
        f.write(f"Total de palavras: {stats['total_palavras']}\n")
        f.write(f"Total de frases: {stats['total_frases']}\n")
        f.write(f"Tamanho médio das frases: {stats['tamanho_medio_frase']:.2f}\n")
        f.write(f"Frase mais longa: {stats['tamanho_max_frase']} palavras\n")
        f.write(f"Frase mais curta: {stats['tamanho_min_frase']} palavras\n\n")

        f.write("=== Vocabulário ===\n")
        f.write(f"TTR: {stats['ttr']:.3f}\n")
        f.write(f"MTLD: {stats['mtld']:.3f}\n")
        f.write(f"HDD: {stats['hdd']:.3f}\n")
        f.write(f"Densidade lexical (por bloco de 100): {stats['densidade_lexical']:.3f}\n")
        f.write(f"Índice de repetição: {stats['indice_repeticao']:.3f}\n\n")

        f.write("=== Vícios e padrões ===\n")
        f.write(f"Advérbios em -mente: {stats['adv_mente']}\n")
        f.write(f"Verbos fracos: {stats['verbos_fracos']}\n\n")

        f.write("=== Top 20 palavras ===\n")
        for palavra, freq in stats["top_20_palavras"]:
            f.write(f"  {palavra}: {freq}\n")
        f.write("\n")

        f.write("=== Diagnóstico Literário™ ===\n")
        for aviso in diagnostico(stats):
            f.write(f"- {aviso}\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FRENÊSI LITERÁRIO™ – Ultimate Edition")
    parser.add_argument("pdf", help="Arquivo PDF de entrada")
    parser.add_argument("saida", help="Arquivo .txt de saída")
    args = parser.parse_args()

    print("Extraindo texto...")
    texto = limpar(extrair_texto_pdf(args.pdf))

    print("Analisando...")
    stats = examinar(texto)

    print("Gerando relatório...")
    salvar_relatorio(stats, args.saida)

    print(f"Relatório gerado em: {args.saida}")

if __name__ == "__main__":
    main()
