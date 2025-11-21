#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANÁLISE AVANÇADA POR CAPÍTULO – PDF

Mede, para cada capítulo:
- Substantivos abstratos vs concretos
- Verbos no gerúndio
- Possíveis nominalizações (ex: "fazer uma caminhada")
- Estatísticas gerais por capítulo e totais

Requisitos:
    pip install pdfminer.six spacy
    python -m spacy download pt_core_news_sm

Uso:
    python analise_capitulos_avancada.py arquivo.pdf relatorio.txt
"""

import re
import os
from collections import defaultdict

from pdfminer.high_level import extract_text
import spacy

# Carrega modelo de português
nlp = spacy.load("pt_core_news_sm")


# ---------- Extração e preparação de texto ----------

def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto bruto de um PDF."""
    return extract_text(caminho_pdf)


def normalizar_espacos(texto: str) -> str:
    """Remove lixo de espaçamento."""
    texto = texto.replace("\r", " ")
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def split_capitulos(texto: str):
    """
    Divide o texto em capítulos usando cabeçalhos do tipo:
    CAPÍTULO 1, Capítulo I, etc.

    Retorna lista de dicts: [{"titulo": ..., "texto": ...}, ...]
    """
    pattern = r'(?im)^(cap[íi]tulo[^\n]*)'
    partes = re.split(pattern, texto)

    if len(partes) <= 1:
        return [{"titulo": "Texto completo", "texto": texto.strip()}]

    capitulos = []
    prefixo = partes[0].strip()
    idx = 1

    if prefixo:
        capitulos.append({"titulo": "Pré-texto", "texto": prefixo})

    while idx < len(partes) - 1:
        titulo = partes[idx].strip()
        corpo = partes[idx + 1].strip()
        capitulos.append({"titulo": titulo, "texto": corpo})
        idx += 2

    return capitulos


# ---------- Heurísticas linguísticas ----------

# Sufixos típicos de substantivos abstratos (bem grosseiro, mas útil)
ABSTRACT_SUFFIXES = (
    "dade", "ção", "são", "mento", "tude", "eza", "ez",
    "agem", "ismo", "ia", "ícia", "ura", "ância", "ência"
)

# Lista manual de abstratos frequentes (emoções, ideias etc.)
ABSTRACT_LEMMAS = {
    "amor", "ódio", "medo", "fé", "esperança", "culpa", "tristeza",
    "alegria", "raiva", "dor", "prazer", "memória", "liberdade",
    "poder", "justiça", "injustiça", "verdade", "mentira",
    "saudade", "vida", "morte", "alma", "orgulho", "vergonha"
}

# Verbos auxiliares típicos de nominalização
NOMINALIZING_VERBS = {
    "fazer", "dar", "ter", "realizar", "efetuar", "executar",
    "promover", "desenvolver"
}


def is_abstract_noun(token) -> bool:
    """Heurística: decide se um substantivo é abstrato."""
    if token.pos_ not in ("NOUN", "PROPN"):
        return False

    lemma = token.lemma_.lower()

    if lemma in ABSTRACT_LEMMAS:
        return True

    for suf in ABSTRACT_SUFFIXES:
        if lemma.endswith(suf):
            return True

    return False


def is_concrete_noun(token) -> bool:
    """Concreto = substantivo que não foi classificado como abstrato."""
    return token.pos_ in ("NOUN", "PROPN") and not is_abstract_noun(token)


def is_gerund_verb(token) -> bool:
    """Detecta verbo no gerúndio via morfologia spaCy."""
    return token.pos_ == "VERB" and "VerbForm=Ger" in token.morph


def contar_nominalizacoes(doc) -> int:
    """
    Conta construções do tipo:
    VERBO (fazer/dar/ter/...) + DET + NOUN deverbal (ex: caminhada, realização, observação)
    """
    count = 0
    tokens = list(doc)
    n = len(tokens)

    for i, tok in enumerate(tokens):
        if tok.pos_ == "VERB" and tok.lemma_.lower() in NOMINALIZING_VERBS:
            # olha adiante um pequeno trecho
            j = i + 1
            while j < n and j <= i + 4:
                if tokens[j].pos_ == "DET":
                    # depois do DET, tenta achar NOUN
                    if j + 1 < n and tokens[j+1].pos_ == "NOUN":
                        noun = tokens[j+1]
                        lemma = noun.lemma_.lower()
                        # se o substantivo tiver sufixo "de ação", provavelmente é nominalização
                        if lemma.endswith(ABSTRACT_SUFFIXES) or lemma.endswith(("ada", "agem")):
                            count += 1
                            break
                j += 1

    return count


# ---------- Análise por capítulo ----------

def analisar_capitulo(texto: str) -> dict:
    """Analisa um capítulo e retorna métricas."""
    texto_norm = normalizar_espacos(texto)
    doc = nlp(texto_norm)

    total_tokens = 0
    total_nouns = 0
    abstract_nouns = 0
    concrete_nouns = 0
    total_verbs = 0
    gerunds = 0

    for token in doc:
        if not token.is_alpha:
            continue
        total_tokens += 1

        if token.pos_ in ("NOUN", "PROPN"):
            total_nouns += 1
            if is_abstract_noun(token):
                abstract_nouns += 1
            else:
                concrete_nouns += 1

        if token.pos_ == "VERB":
            total_verbs += 1
            if is_gerund_verb(token):
                gerunds += 1

    nominalizacoes = contar_nominalizacoes(doc)

    # porcentagens/razões
    pct_abstract = abstract_nouns / total_nouns * 100 if total_nouns else 0.0
    pct_concrete = concrete_nouns / total_nouns * 100 if total_nouns else 0.0
    verb_density = total_verbs / total_tokens * 100 if total_tokens else 0.0
    gerund_pct = gerunds / total_verbs * 100 if total_verbs else 0.0
    nominalizacoes_por_10k = nominalizacoes / total_tokens * 10000 if total_tokens else 0.0

    return {
        "tokens": total_tokens,
        "substantivos_total": total_nouns,
        "substantivos_abstratos": abstract_nouns,
        "substantivos_concretos": concrete_nouns,
        "pct_abstratos": pct_abstract,
        "pct_concretos": pct_concrete,
        "verbos_total": total_verbs,
        "verbos_gerundio": gerunds,
        "pct_gerundio": gerund_pct,
        "densidade_verbal_pct": verb_density,
        "nominalizacoes": nominalizacoes,
        "nominalizacoes_por_10k": nominalizacoes_por_10k,
    }


# ---------- Relatório ----------

def gerar_alertas(stats_global: dict) -> list:
    """Gera alguns alertas gerais com base nos dados agregados."""
    avisos = []

    # proporção abstrato/concreto
    if stats_global["pct_abstratos"] > 60:
        avisos.append("MUITO abstrato: mais de 60% dos substantivos parecem abstratos.")
    elif stats_global["pct_abstratos"] < 25:
        avisos.append("Pouca abstração: menos de 25% dos substantivos são abstratos.")

    # densidade verbal
    if stats_global["densidade_verbal_pct"] < 10:
        avisos.append("Poucos verbos: narrativa potencialmente lenta e descritiva.")
    elif stats_global["densidade_verbal_pct"] > 25:
        avisos.append("Muitos verbos: narrativa pode estar excessivamente acelerada.")

    # gerúndio
    if stats_global["pct_gerundio"] > 10:
        avisos.append("Uso alto de gerúndio: pode haver arrasto em frases (estar fazendo, estar falando...).")

    # nominalização
    if stats_global["nominalizacoes_por_10k"] > 30:
        avisos.append("Muitas nominalizações: padrões tipo 'fazer uma caminhada' aparecem com frequência.")

    if not avisos:
        avisos.append("Distribuição global razoavelmente equilibrada. Nenhum problema grave detectado.")

    return avisos


def salvar_relatorio(capitulos_stats, caminho_saida: str):
    """Gera relatório em texto com tabela por capítulo e resumo global."""
    # Agregar globais
    glob = defaultdict(float)
    for st in capitulos_stats:
        for k, v in st["stats"].items():
            if isinstance(v, (int, float)):
                glob[k] += v

    # Recalcular percentuais globais
    if glob["substantivos_total"]:
        glob["pct_abstratos"] = glob["substantivos_abstratos"] / glob["substantivos_total"] * 100
        glob["pct_concretos"] = glob["substantivos_concretos"] / glob["substantivos_total"] * 100
    else:
        glob["pct_abstratos"] = glob["pct_concretos"] = 0.0

    if glob["tokens"]:
        glob["densidade_verbal_pct"] = glob["verbos_total"] / glob["tokens"] * 100
        glob["nominalizacoes_por_10k"] = glob["nominalizacoes"] / glob["tokens"] * 10000
    else:
        glob["densidade_verbal_pct"] = glob["nominalizacoes_por_10k"] = 0.0

    if glob["verbos_total"]:
        glob["pct_gerundio"] = glob["verbos_gerundio"] / glob["verbos_total"] * 100
    else:
        glob["pct_gerundio"] = 0.0

    avisos = gerar_alertas(glob)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("ANÁLISE AVANÇADA POR CAPÍTULO – SUBSTANTIVOS / GERÚNDIO / NOMINALIZAÇÃO\n")
        f.write("=========================================================================\n\n")

        f.write("RESUMO GLOBAL\n")
        f.write("-------------\n")
        f.write(f"Tokens totais: {int(glob['tokens'])}\n")
        f.write(f"Substantivos (total): {int(glob['substantivos_total'])}\n")
        f.write(f"  Abstratos: {int(glob['substantivos_abstratos'])} ({glob['pct_abstratos']:.2f}%)\n")
        f.write(f"  Concretos: {int(glob['substantivos_concretos'])} ({glob['pct_concretos']:.2f}%)\n")
        f.write(f"Verbos (total): {int(glob['verbos_total'])}\n")
        f.write(f"  Gerúndio: {int(glob['verbos_gerundio'])} ({glob['pct_gerundio']:.2f}%)\n")
        f.write(f"Densidade verbal: {glob['densidade_verbal_pct']:.2f}% dos tokens\n")
        f.write(f"Nominalizações detectadas (total): {int(glob['nominalizacoes'])}\n")
        f.write(f"Nominalizações por 10.000 palavras: {glob['nominalizacoes_por_10k']:.2f}\n\n")

        f.write("ALERTAS GERAIS\n")
        f.write("--------------\n")
        for a in avisos:
            f.write(f"- {a}\n")
        f.write("\n")

        # Tabela comparativa por capítulo
        f.write("TABELA POR CAPÍTULO\n")
        f.write("-------------------\n\n")
        f.write("{:<25} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8}\n".format(
            "Capítulo", "Tokens", "Subst", "Abstr%", "Verbos", "Gerund%", "Nom/10k"
        ))
        f.write("-" * 80 + "\n")

        for cap in capitulos_stats:
            t = cap["titulo"][:25]
            st = cap["stats"]
            f.write("{:<25} {:>8} {:>8} {:>8.1f} {:>8} {:>8.1f} {:>8.1f}\n".format(
                t,
                st["tokens"],
                st["substantivos_total"],
                st["pct_abstratos"],
                st["verbos_total"],
                st["pct_gerundio"],
                st["nominalizacoes_por_10k"],
            ))

        f.write("\n\nREFERÊNCIA (interpretação aproximada)\n")
        f.write("-------------------------------------\n")
        f.write("• Subst. abstratos > 60% → texto muito conceitual / ensaístico.\n")
        f.write("• Densidade verbal 12–20% → narrativa em ritmo normal.\n")
        f.write("• Gerúndio > 10% dos verbos → possível arrasto em frases.\n")
        f.write("• Nominalizações altas → muitos padrões tipo 'fazer uma caminhada' em vez de 'caminhar'.\n")


# ---------- Main ----------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Análise capítulo a capítulo (PDF)")
    parser.add_argument("pdf", help="Arquivo PDF de entrada")
    parser.add_argument("saida", help="Arquivo .txt de relatório")
    args = parser.parse_args()

    print("Lendo PDF...")
    texto = extrair_texto_pdf(args.pdf)

    print("Normalizando texto...")
    texto_norm = normalizar_espacos(texto)

    print("Dividindo em capítulos...")
    capitulos = split_capitulos(texto_norm)

    capitulos_stats = []
    print(f"Encontrados {len(capitulos)} capítulos/segmentos.")

    for cap in capitulos:
        print(f"Analisando: {cap['titulo']}")
        stats = analisar_capitulo(cap["texto"])
        capitulos_stats.append({"titulo": cap["titulo"], "stats": stats})

    print("Gerando relatório...")
    salvar_relatorio(capitulos_stats, args.saida)

    print("Concluído.")
    print(f"Relatório salvo em: {args.saida}")


if __name__ == "__main__":
    main()