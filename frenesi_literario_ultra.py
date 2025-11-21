#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FRENÊSI LITERÁRIO™ ULTRA

Analisador estilístico para texto de ficção extraído de PDF.

Funcionalidades:
- Extrai texto de PDF
- Divide em capítulos (por padrão, cabeçalhos "CAPÍTULO X")
- Calcula métricas globais e por capítulo:
    - total de palavras / frases
    - tamanho médio das frases
    - TTR, MTLD, HDD (LexicalRichness)
    - densidade lexical por blocos
    - índice de repetição
    - contagem de advérbios em -mente
    - verbos fracos e fortes
    - top 20 palavras (sem stopwords)
    - Nota FRENÊSI™ (0–100) e diagnóstico

- Gera:
    - relatório em texto (.txt)
    - arquivo de texto com destaques:
        [FRACO: verbo], [FORTE: verbo], [ADV: palavra]

Requisitos:
    pip install pdfminer.six spacy lexicalrichness
    python -m spacy download pt_core_news_sm
"""

import os
import re
import statistics
from collections import Counter

from pdfminer.high_level import extract_text
from lexicalrichness import LexicalRichness
import spacy
from spacy.lang.pt.stop_words import STOP_WORDS

# Carrega modelo do spaCy
nlp = spacy.load("pt_core_news_sm")

# Stopwords em português
STOPWORDS = set(STOP_WORDS)

# Verbos fracos (ajustável)
VERBOS_FRACOS = {
    # Existenciais / vazios
    "ser", "estar", "ter", "haver", "existir", "acontecer", "ocorrer",

    # Ligação
    "ficar", "parecer", "continuar", "permanecer", "tornar-se",
    "manter-se", "virar", "voltar-se",

    # Auxiliares
    "poder", "dever", "precisar", "costumar",
    "querer", "tentar", "conseguir", "deixar",

    # Cognitivos genéricos
    "achar", "pensar", "imaginar", "acreditar",
    "notar", "perceber", "sentir", "ver", "saber",

    # Genéricos universais
    "fazer", "colocar", "passar", "botar", "pegar", "voltar",

    # Conversacionais fracos
    "dizer", "falar", "comentar", "contar",
    "perguntar", "responder",

    # Descritivos vazios
    "aparecer", "surgir", "ir", "vir"
}

# Verbos fortes (ajustável)
VERBOS_FORTES = {
    "avançar", "atirar", "erguer", "arremessar", "agarrar", "arrastar",
    "golpear", "correr", "disparar", "desabar", "investir", "lançar",
    "rasgar", "puxar", "empurrar", "invadir", "mergulhar", "tombar",
    "derrubar", "cravar", "pular", "arrebentar", "esmagar", "socar",

    "encarar", "espiar", "detectar", "farejar", "examinar", "vasculhar",
    "observar", "apalpar", "reconhecer", "fitar",

    "ameaçar", "provocar", "confrontar", "acusar", "pressionar",
    "encurralar", "dominar", "intimidar", "desafiar", "subjugar",
    "interrogar",

    "latejar", "ressoar", "tremeçar", "contrair", "vibrar", "pulsar",
    "engolir", "sufocar",

    "romper", "quebrar", "transformar", "distorcer", "moldar", "curvar",
    "gelar", "aquecer", "converter", "estilhaçar", "enrijecer",

    "decidir", "afirmar", "insistir", "negar", "jurar", "ordenar",
    "convocar", "implorar",

    "ecoar", "silvar", "estalhar", "vazar", "chorar", "zumbir",
    "chispar", "estourar",

    "agredir", "acariciar", "consolar", "afastar", "aproximar",
    "abrigar", "socorrer", "amparar", "abraçar", "segurar",

    "rosnar", "grunhir", "sussurrar", "berrar", "murmurar", "bufar",
    "retrucar", "gritar", "soltar", "vomitar"
}

def frases_numeradas_somente_marcadas(texto: str):
    """
    Divide o texto em frases e mantém apenas as que têm marcações
    [FRACO:], [FORTE:], [ADV:].
    Numeradas.
    """
    # Divide sem usar spaCy para preservar marcações
    frases = re.split(r'(?<=[.!?])\s+', texto)

    linhas = []
    n = 1

    for f in frases:
        frase = f.strip()

        # mantém só as que têm alguma etiqueta
        if ("[FRACO:" in frase or
            "[FORTE:" in frase or
            "[ADV:" in frase):

            linhas.append(f"{n}. {frase}")
            n += 1

    return "\n".join(linhas)

def frases_numeradas_preservando(texto: str):
    """
    Divide o texto em frases mantendo qualquer marcação
    (como [FRACO:], [FORTE:]) intacta.
    Não usa spaCy, usa regex.
    """
    # Divide após ., ?, ou ! seguidos de espaço
    frases = re.split(r'(?<=[.!?])\s+', texto)

    linhas = []
    n = 1
    for f in frases:
        frase = f.strip()
        if frase:
            linhas.append(f"{n}. {frase}")
            n += 1

    return "\n".join(linhas)


def remover_dialogos(texto: str) -> str:
    """
    Remove diálogos entre aspas e linhas iniciadas por travessão.
    Mantém apenas a narrativa.
    """

    # Remove trechos entre aspas “ ”
    texto = re.sub(r"[\"“”](.*?)[\"“”]", "", texto)

    # Remove linhas que começam com travessão — (casos clássicos de diálogo)
    linhas = texto.split("\n")
    linhas_filtradas = [l for l in linhas if not l.strip().startswith("—")]

    return "\n".join(linhas_filtradas)

def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto bruto de um arquivo PDF."""
    return extract_text(caminho_pdf)


def limpar(texto: str) -> str:
    """Limpa quebras de linha excessivas e normaliza espaços."""
    texto = texto.replace("\r", " ")
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def segmentar_frases(texto: str):
    """Segmenta texto em frases usando spaCy."""
    doc = nlp(texto)
    return [sent.text for sent in doc.sents if sent.text.strip()]


def split_capitulos(texto_bruto: str):
    """
    Divide o texto em capítulos com base em cabeçalhos do tipo:
    'CAPÍTULO 1', 'Capítulo I', etc.

    Se não encontrar nenhum padrão, retorna um capítulo único.
    """
    pattern = r'(?im)^(cap[íi]tulo\s+[^\n]+)'
    partes = re.split(pattern, texto_bruto)

    capitulos = []

    if len(partes) <= 1:
        # Não encontrou nenhum cabeçalho de capítulo
        capitulos.append({
            "titulo": "Texto completo",
            "texto": texto_bruto.strip()
        })
        return capitulos

    # partes = [antes, titulo1, texto1, titulo2, texto2, ...]
    # ignorar "antes" se for só lixo
    prefixo = partes[0].strip()
    idx = 1

    if prefixo:
        capitulos.append({
            "titulo": "Pré-texto",
            "texto": prefixo
        })

    while idx < len(partes) - 1:
        titulo = partes[idx].strip()
        corpo = partes[idx + 1].strip()
        capitulos.append({
            "titulo": titulo,
            "texto": corpo
        })
        idx += 2

    return capitulos


def densidade_lexical(texto: str, janela: int = 100) -> float:
    """Calcula TTR médio em blocos de tamanho fixo."""
    palavras = re.findall(r"\w+", texto.lower())
    if not palavras:
        return 0.0
    blocos = [palavras[i:i + janela] for i in range(0, len(palavras), janela)]
    ttrs = [len(set(b)) / len(b) for b in blocos if len(b) == janela]
    return sum(ttrs) / len(ttrs) if ttrs else 0.0


def indice_repeticao(texto: str) -> float:
    """Proporção de repetição lexical: 1 - (types/tokens)."""
    palavras = re.findall(r"\w+", texto.lower())
    if not palavras:
        return 0.0
    return 1 - (len(set(palavras)) / len(palavras))


def frenesi_score(stats: dict) -> float:
    """Calcula uma Nota FRENÊSI™ de 0 a 100 a partir das métricas."""
    score = 50.0

    # TTR
    ttr = stats.get("ttr", 0)
    if 0.20 <= ttr <= 0.40:
        score += 10
    elif ttr < 0.18 or ttr > 0.45:
        score -= 5

    # MTLD
    mtld = stats.get("mtld", 0)
    if mtld >= 50:
        score += 10
    elif mtld < 30:
        score -= 5

    # Verbos fortes vs fracos
    vf = stats.get("verbos_fortes", 0)
    vfr = stats.get("verbos_fracos", 0)
    total_v = vf + vfr
    ratio_fortes = vf / total_v if total_v > 0 else 0
    stats["ratio_verbos_fortes"] = ratio_fortes

    if ratio_fortes >= 0.25:
        score += 10
    elif ratio_fortes < 0.10 and total_v > 0:
        score -= 10

    # Advérbios em -mente
    adv_mente = stats.get("adv_mente", 0)
    total_palavras = max(stats.get("total_palavras", 0), 1)
    adv_pct = adv_mente / total_palavras
    if adv_pct > 0.03:
        score -= 5

    # Índice de repetição
    rep = stats.get("indice_repeticao", 0)
    if rep < 0.78:
        score += 5
    elif rep > 0.88:
        score -= 5

    # Tamanho médio das frases
    tmf = stats.get("tamanho_medio_frase", 0)
    if 12 <= tmf <= 24:
        score += 5
    elif tmf > 32 or tmf < 8:
        score -= 5

    # Clamp 0–100
    score = max(0.0, min(100.0, score))
    return score


def diagnostico(stats: dict):
    """Gera diagnóstico textual a partir das métricas."""
    avisos = []

    ttr = stats.get("ttr", 0)
    if ttr < 0.18:
        avisos.append("Vocabulário repetitivo (TTR baixo). Reforçar sinônimos.")
    elif ttr > 0.45:
        avisos.append("Vocabulário muito alto (TTR alto). Cuidado para não soar artificial.")

    if stats.get("adv_mente", 0) > 25:
        avisos.append("Uso elevado de advérbios em -mente. Risco de prosa açucarada.")

    vfr = stats.get("verbos_fracos", 0)
    total_palavras = max(stats.get("total_palavras", 0), 1)
    if vfr > total_palavras * 0.06:
        avisos.append("Alta incidência de verbos fracos. Narrativa pode estar passiva.")

    tmf = stats.get("tamanho_medio_frase", 0)
    if tmf > 28:
        avisos.append("Frases muito longas em média. Considerar cortes e quebras.")
    elif tmf < 10 and tmf > 0:
        avisos.append("Frases curtas demais em média. Risco de estilo telegráfico.")

    rep = stats.get("indice_repeticao", 0)
    if rep > 0.88:
        avisos.append("Repetição lexical elevada. Pode haver barriga narrativa.")
    elif rep < 0.75 and stats.get("total_palavras", 0) > 500:
        avisos.append("Baixa repetição lexical para texto longo. Ver se não há excesso de variação gratuita.")

    if not avisos:
        avisos.append("Estilisticamente saudável. Nenhum problema evidente nas métricas gerais.")

    return avisos


def examinar_texto(texto: str) -> dict:
    """Executa toda a análise em um trecho de texto."""
    texto_limpo = limpar(texto)

    palavras = re.findall(r"\w+", texto_limpo.lower())
    total_palavras = len(palavras)

    # Frases
    frases = segmentar_frases(texto_limpo)
    tamanhos_frase = [len(f.split()) for f in frases] if frases else []

    # Vocabulário
    palavras_filtradas = [p for p in palavras if p not in STOPWORDS]
    contador = Counter(palavras_filtradas)

    # LexicalRichness
    if texto_limpo.strip():
        lex = LexicalRichness(texto_limpo)
        ttr = lex.ttr
        mtld = lex.mtld()
        hdd = lex.hdd()
    else:
        ttr = mtld = hdd = 0.0

    # Advérbios em -mente
    adv_mente = [p for p in palavras if p.endswith("mente")]

    # Verbos fracos / fortes (por string simples)
    verbos_fracos = [p for p in palavras if p in VERBOS_FRACOS]
    verbos_fortes = [p for p in palavras if p in VERBOS_FORTES]

    stats = {
        "total_palavras": total_palavras,
        "total_frases": len(frases),
        "tamanho_medio_frase": statistics.mean(tamanhos_frase) if tamanhos_frase else 0.0,
        "tamanho_max_frase": max(tamanhos_frase) if tamanhos_frase else 0,
        "tamanho_min_frase": min(tamanhos_frase) if tamanhos_frase else 0,
        "top_20_palavras": contador.most_common(20),
        "adv_mente": len(adv_mente),
        "verbos_fracos": len(verbos_fracos),
        "verbos_fortes": len(verbos_fortes),
        "ttr": ttr,
        "mtld": mtld,
        "hdd": hdd,
        "densidade_lexical": densidade_lexical(texto_limpo),
        "indice_repeticao": indice_repeticao(texto_limpo),
    }

    # Nota FRENÊSI™
    stats["nota_frenesi"] = frenesi_score(stats)

    return stats


def gerar_highlight(texto: str) -> str:
    """
    Gera uma versão do texto com destaques:
    - [FRACO: palavra]
    - [FORTE: palavra]
    - [ADV: palavra] para advérbios em -mente
    """
    resultado = []
    # separa palavras e não-palavras para preservar espaçamento
    tokens = re.findall(r"\w+|\W+", texto)

    for tok in tokens:
        if tok.strip() and re.match(r"\w+", tok):
            base = tok.lower()
            if base in VERBOS_FRACOS:
                resultado.append(f"[FRACO:{tok}]")
            elif base in VERBOS_FORTES:
                resultado.append(f"[FORTE:{tok}]")
            elif base.endswith("mente"):
                resultado.append(f"[ADV:{tok}]")
            else:
                resultado.append(tok)
        else:
            resultado.append(tok)

    return "".join(resultado)


def salvar_relatorio(global_stats: dict, capitulos_stats: list, caminho_saida: str):
    """Salva o relatório textual completo no arquivo indicado."""
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write("FRENÊSI LITERÁRIO™ ULTRA – Relatório Completo\n")
        f.write("=============================================\n\n")

        f.write("=== MÉTRICAS GLOBAIS ===\n")
        f.write(f"Total de palavras: {global_stats['total_palavras']}\n")
        f.write(f"Total de frases: {global_stats['total_frases']}\n")
        f.write(f"Tamanho médio das frases: {global_stats['tamanho_medio_frase']:.2f}\n")
        f.write(f"Frase mais longa: {global_stats['tamanho_max_frase']} palavras\n")
        f.write(f"Frase mais curta: {global_stats['tamanho_min_frase']} palavras\n\n")

        f.write("=== VOCABULÁRIO ===\n")
        f.write(f"TTR: {global_stats['ttr']:.3f}\n")
        f.write(f"MTLD: {global_stats['mtld']:.3f}\n")
        f.write(f"HDD: {global_stats['hdd']:.3f}\n")
        f.write(f"Densidade lexical (por bloco de 100): {global_stats['densidade_lexical']:.3f}\n")
        f.write(f"Índice de repetição: {global_stats['indice_repeticao']:.3f}\n\n")

        f.write("=== VERBOS E ADVÉRBIOS ===\n")
        f.write(f"Verbos fracos: {global_stats['verbos_fracos']}\n")
        f.write(f"Verbos fortes: {global_stats['verbos_fortes']}\n")
        total_v = global_stats['verbos_fracos'] + global_stats['verbos_fortes']
        if total_v > 0:
            ratio_f = global_stats['verbos_fortes'] / total_v
        else:
            ratio_f = 0.0
        f.write(f"Proporção de verbos fortes: {ratio_f:.3f}\n")
        f.write(f"Advérbios em -mente: {global_stats['adv_mente']}\n\n")

        f.write("=== TOP 20 PALAVRAS (sem stopwords) ===\n")
        for palavra, freq in global_stats["top_20_palavras"]:
            f.write(f"  {palavra}: {freq}\n")
        f.write("\n")

        f.write("=== NOTA FRENÊSI™ GLOBAL ===\n")
        f.write(f"Nota: {global_stats['nota_frenesi']:.1f} / 100\n\n")

        f.write("=== DIAGNÓSTICO GLOBAL ===\n")
        for aviso in diagnostico(global_stats):
            f.write(f"- {aviso}\n")
        f.write("\n")

        f.write("=============================================\n")
        f.write("=== ANÁLISE POR CAPÍTULO ===\n\n")

        for cap in capitulos_stats:
            titulo = cap["titulo"]
            stats = cap["stats"]
            f.write(f"--- {titulo} ---\n")
            f.write(f"Palavras: {stats['total_palavras']} | Frases: {stats['total_frases']}\n")
            f.write(f"Tamanho médio das frases: {stats['tamanho_medio_frase']:.2f}\n")
            f.write(f"Verbos fracos: {stats['verbos_fracos']} | Verbos fortes: {stats['verbos_fortes']}\n")
            total_vc = stats['verbos_fortes'] + stats['verbos_fracos']
            ratio_fc = stats['verbos_fortes'] / total_vc if total_vc > 0 else 0.0
            f.write(f"Proporção de verbos fortes: {ratio_fc:.3f}\n")
            f.write(f"TTR: {stats['ttr']:.3f} | MTLD: {stats['mtld']:.3f} | HDD: {stats['hdd']:.3f}\n")
            f.write(f"Nota FRENÊSI™ do capítulo: {stats['nota_frenesi']:.1f}\n")

            for aviso in diagnostico(stats):
                f.write(f"- {aviso}\n")

            f.write("\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="FRENÊSI LITERÁRIO™ ULTRA – Analisador de PDF")
    parser.add_argument("pdf", help="Arquivo PDF de entrada")
    parser.add_argument("saida", help="Arquivo .txt de saída (relatório)")
    args = parser.parse_args()

    print("Extraindo texto do PDF...")
    texto_bruto = extrair_texto_pdf(args.pdf)

    print("Removendo diálogos...")
    texto_bruto = remover_dialogos(texto_bruto)

    print("Dividindo em capítulos...")
    capitulos = split_capitulos(texto_bruto)

    # Texto global (limpo) para análise geral
    print("Preparando texto global...")
    texto_global = " ".join(limpar(c["texto"]) for c in capitulos)

    print("Analisando texto global...")
    global_stats = examinar_texto(texto_global)

    print("Analisando capítulos...")
    capitulos_stats = []
    for cap in capitulos:
        stats_cap = examinar_texto(cap["texto"])
        capitulos_stats.append({
            "titulo": cap["titulo"],
            "stats": stats_cap
        })

    print("Gerando relatório...")
    salvar_relatorio(global_stats, capitulos_stats, args.saida)

    # Gera texto com destaques
    base, ext = os.path.splitext(args.saida)
    destaque_path = base + "_highlight.txt"
    print("Gerando texto com destaques...")
    texto_destacado = gerar_highlight(texto_global)
    #texto_destacado = frases_numeradas_preservando(texto_destacado)
    texto_destacado = frases_numeradas_somente_marcadas(texto_destacado)


    with open(destaque_path, "w", encoding="utf-8") as fh:
        fh.write(texto_destacado)

    print(f"Relatório salvo em: {args.saida}")
    print(f"Texto destacado salvo em: {destaque_path}")


if __name__ == "__main__":
    main()
