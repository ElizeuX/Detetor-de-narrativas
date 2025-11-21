import pandas as pd
from pypdf import PdfReader
import re
import os
from datetime import datetime
from collections import defaultdict # Para agrupar as variantes dos nomes

# --- FUNÇÕES DE EXTRAÇÃO (Reutilizadas) ---

def extrair_texto_de_pdf(caminho_arquivo):
    """
    Lê o PDF no caminho especificado e retorna todo o seu conteúdo como texto.
    """
    texto_completo = ""
    try:
        reader = PdfReader(caminho_arquivo)
        for page in reader.pages:
            texto_completo += page.extract_text() + "\n"
        return texto_completo
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Ocorreu um erro durante a leitura do PDF: {e}")
        return None

# --- FUNÇÃO PRINCIPAL: VERIFICAR CONSISTÊNCIA ---

def verificar_consistencia_nomes(texto, min_ocorrencias=5):
    """
    1. Encontra possíveis nomes próprios (palavras capitalizadas).
    2. Agrupa as diferentes formas de escrita de um mesmo nome (ignorando case).
    3. Identifica as inconsistências onde há mais de uma variante.
    """
    if not texto:
        return {}

    # 1. Encontrar todos os possíveis nomes próprios (palavras que começam com maiúscula)
    # A regex busca palavras com 3 ou mais letras que iniciam com maiúscula,
    # excluindo o início de frases comuns (ex: 'O', 'A', 'E', 'De').
    # Isso é um filtro heurístico e pode não ser 100% preciso, mas é um bom começo.
    padrao_nomes = r'\b[A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*\b'
    nomes_encontrados = re.findall(padrao_nomes, texto)

    # 2. Agrupar variantes
    # A chave do dicionário será a forma minúscula do nome (a base)
    # O valor será um conjunto (set) das formas variantes encontradas no texto.
    variantes = defaultdict(lambda: defaultdict(int)) # {nome_base: {variante: contagem}}

    for nome in nomes_encontrados:
        nome_base = nome.lower()
        # Ignoramos nomes curtos ou palavras que podem ser o início de frases
        if len(nome_base) < 4:
             continue
        variantes[nome_base][nome] += 1

    # 3. Identificar Inconsistências
    inconsistencias = {}

    for nome_base, variantes_encontradas in variantes.items():
        total_ocorrencias = sum(variantes_encontradas.values())

        # Filtra por nomes que ocorrem poucas vezes para evitar falsos positivos
        if total_ocorrencias < min_ocorrencias:
            continue

        # Se houver mais de uma forma diferente de escrita (ex: 'Gandalf' e 'Gandalf')
        # ou se houver maiúsculas e minúsculas diferentes (ex: 'Frodo' e 'Frodo')
        if len(variantes_encontradas) > 1:
            inconsistencias[nome_base] = variantes_encontradas

    return inconsistencias

# --- 3. FUNÇÃO GERAR RELATÓRIO ---

def gerar_relatorio(caminho_arquivo, inconsistencias, min_ocorrencias):
    """
    Gera uma string de relatório e a salva em um arquivo de texto.
    """
    nome_saida = "relatorio_consistencia_nomes.txt"

    relatorio = "=========================================================\n"
    relatorio += "| RELATÓRIO DE VERIFICAÇÃO DE CONSISTÊNCIA DE NOMES |\n"
    relatorio += "=========================================================\n"
    relatorio += f"Data da Análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    relatorio += f"Arquivo Fonte: {caminho_arquivo}\n"
    relatorio += f"Limite Mínimo de Ocorrências (Para Análise): {min_ocorrencias}\n"
    relatorio += "\n--- INCONSISTÊNCIAS DETECTADAS ---\n\n"

    if not inconsistencias:
        relatorio += "✅ Nenhuma inconsistência de escrita significativa (variantes) foi encontrada nos nomes próprios.\n"
    else:
        for nome_base, variantes in inconsistencias.items():
            relatorio += f"⚠️ NOME BASE: '{nome_base.upper()}'\n"
            relatorio += "   VARIAÇÕES ENCONTRADAS:\n"

            # Formata a lista de variantes
            for variante, contagem in variantes.items():
                relatorio += f"   - '{variante}' (Ocorrências: {contagem})\n"

            relatorio += f"   TOTAL GERAL: {sum(variantes.values())} Ocorrências.\n"
            relatorio += "   --------------------------\n"

    # Salvar o relatório em arquivo
    try:
        with open(nome_saida, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        return relatorio, nome_saida
    except Exception as e:
        return f"Erro ao escrever arquivo: {e}", None

# --- Bloco Principal de Execução ---
if __name__ == "__main__":

    # 📌 CONFIGURAÇÕES
    caminho_do_arquivo = 'main.pdf'
    min_ocorrencias = 5  # Nome deve aparecer pelo menos 5 vezes para ser verificado

    print(f"--- 🔎 Verificador de Consistência de Nomes ---")

    if not os.path.exists(caminho_do_arquivo):
        print(f"❌ Erro: Arquivo '{caminho_do_arquivo}' não encontrado. Usando texto de demonstração.")
        # Texto de demonstração com inconsistências
        texto_para_analisar = """
        O herói, **Kaelin**, partiu para a Montanha Solitária. Ele encontrou seu guia,
        um anão chamado **Bryn**. Kaelin caminhou por dias. O anão **Brynn** insistia
        que eles parassem. O mago **Xylar** apareceu, mas Kaelin desconfiou.
        Kaelin continuou. O mago **XYLAR** riu. O Kaelin estava exausto.
        O **Kaelin** é teimoso. Finalmente, **Bryn** desistiu. No final, o herói **kaelin**
        salvou o dia. (Muitas ocorrências para forçar a verificação)
        """ * 5
        caminho_do_arquivo = "[DEMONSTRAÇÃO]"
    else:
        print(f"⏳ Extraindo texto do PDF: {caminho_do_arquivo}...")
        texto_para_analisar = extrair_texto_de_pdf(caminho_do_arquivo)


    if texto_para_analisar:
        print(f"✅ Texto pronto. Analisando consistência de nomes...")

        # VERIFICAR CONSISTÊNCIA
        inconsistencias = verificar_consistencia_nomes(texto_para_analisar, min_ocorrencias)

        # GERAR E SALVAR RELATÓRIO
        relatorio_saida, nome_saida = gerar_relatorio(caminho_do_arquivo, inconsistencias, min_ocorrencias)

        # IMPRIMIR O RELATÓRIO NO CONSOLE E INFORMAR O ARQUIVO
        print("\n" + relatorio_saida)

        if nome_saida:
            print("\n" + "="*70)
            print(f"SUCESSO! Relatório de Consistência salvo em: **{nome_saida}**")
            print("==========================================================")
    else:
        print("⚠️ O texto extraído está vazio ou a extração falhou.")