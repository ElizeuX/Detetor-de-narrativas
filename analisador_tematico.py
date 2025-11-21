import pandas as pd
from pypdf import PdfReader
import re
import os
from datetime import datetime
from collections import Counter
import nltk
from nltk.corpus import stopwords

# Tenta baixar a lista de stopwords se ainda não foi baixada
try:
    STOPWORDS_PT = set(stopwords.words('portuguese'))
except LookupError:
    print("Baixando 'stopwords' do NLTK...")
    nltk.download('stopwords')
    STOPWORDS_PT = set(stopwords.words('portuguese'))

# --- FUNÇÕES DE EXTRAÇÃO ---

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

# --- FUNÇÃO PRINCIPAL: ANÁLISE DE FREQUÊNCIA ---

def analisar_frequencia_tematica(texto, palavras_a_excluir=None, min_tamanho_palavra=3, top_n=50):
    """
    Processa o texto, remove stopwords e pontuação, e conta a frequência
    das palavras restantes (os temas e keywords).
    """
    if not texto:
        return pd.DataFrame(), 0

    # 1. Pré-processamento e Tokenização
    # Remove pontuação e caracteres especiais, exceto espaços e hífens internos
    # Inclui acentuação em minúsculas
    texto_limpo = re.sub(r'[^a-záéíóúàèìòùâêîôûãõç\s-]', '', texto.lower())

    # Divide o texto em tokens (palavras)
    tokens = texto_limpo.split()

    # Combina a lista padrão de stopwords com quaisquer palavras extras
    palavras_excluidas = STOPWORDS_PT.union(set(palavras_a_excluir or []))

    # 2. Filtragem de Palavras Relevantes
    palavras_relevantes = [
        palavra
        for palavra in tokens
        if palavra not in palavras_excluidas and len(palavra) >= min_tamanho_palavra
    ]

    total_palavras_analisadas = len(palavras_relevantes)

    # 3. Contagem de Frequência
    contagens = Counter(palavras_relevantes)

    # 4. Preparação do DataFrame
    df = pd.DataFrame(contagens.most_common(top_n), columns=['Palavra-Chave', 'Frequência'])

    # Cálculo da Frequência Percentual
    if total_palavras_analisadas > 0:
        df['Frequência (%)'] = (df['Frequência'] / total_palavras_analisadas * 100).round(2)
    else:
        df['Frequência (%)'] = 0.0

    return df, len(tokens) # Retorna o DataFrame das TOP N e o total de palavras do texto original

# --- 3. FUNÇÃO GERAR RELATÓRIO (CORRIGIDA) ---

def gerar_relatorio_tematico(caminho_arquivo, df_frequencia, total_palavras_brutas, top_n, min_tamanho_palavra):
    """
    Gera uma string de relatório formatada e a salva em um arquivo de texto.

    A correção incluiu 'min_tamanho_palavra' como parâmetro.
    """
    nome_saida = "relatorio_frequencia_tematica.txt"

    relatorio = "=========================================================\n"
    relatorio += "| RELATÓRIO DE ANÁLISE DE FREQUÊNCIA TEMÁTICA |\n"
    relatorio += "=========================================================\n"
    relatorio += f"Data da Análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    relatorio += f"Arquivo Fonte: {caminho_arquivo}\n"
    relatorio += f"Total de Palavras Brutas no Texto: {total_palavras_brutas}\n"
    # CORRIGIDO: Agora min_tamanho_palavra está acessível como parâmetro
    relatorio += f"Palavras Comuns (Stopwords) e Curta (mín={min_tamanho_palavra}) Excluídas.\n"
    relatorio += f"\n--- TOP {top_n} PALAVRAS-CHAVE MAIS FREQUENTES ---\n\n"

    if df_frequencia.empty:
        relatorio += "Não foi possível calcular a frequência de palavras-chave. Texto muito curto ou vazio.\n"
    else:
        # Adiciona a tabela de resultados
        relatorio += df_frequencia.to_string(index=False)
        relatorio += "\n\n"
        relatorio += "INTERPRETAÇÃO:\n"
        relatorio += "A coluna 'Palavra-Chave' indica os principais focos temáticos do seu texto.\n"
        relatorio += "Alta 'Frequência (%)' sugere que o tema é central e recorrente.\n"

    # Salvar o relatório em arquivo
    try:
        with open(nome_saida, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        return relatorio, nome_saida
    except Exception as e:
        return f"Erro ao escrever arquivo: {e}", None

# --- Bloco Principal de Execução (CORRIGIDO) ---
if __name__ == "__main__":

    # 📌 CONFIGURAÇÕES
    caminho_do_arquivo = 'main.pdf'
    top_n_palavras = 50

    # Variável de configuração formalizada para ser passada às funções
    MIN_TAMANHO_PALAVRA = 3

    # Adicione aqui nomes de personagens específicos ou palavras muito comuns que você quer ignorar
    palavras_extras_excluir = {'elizeu', 'montanha', 'castelo'}

    print(f"--- 📊 Analisador de Frequência Temática ---")

    if not os.path.exists(caminho_do_arquivo):
        print(f"❌ Erro: Arquivo '{caminho_do_arquivo}' não encontrado. Usando texto de demonstração.")
        # Texto de demonstração
        texto_para_analisar = """
        O **dragão** voou sobre o **castelo** de Elizeu. O **tesouro** era o objetivo.
        Muitos dragões haviam falhado antes. O **tesouro** estava bem guardado.
        Elizeu defendia o **castelo** e seu **tesouro**. O **dragão** era enorme.
        A batalha pelo **tesouro** e o **castelo** começou.
        O **dragão** atacou. (Repetir esta estrutura para gerar dados)
        """ * 15
        caminho_do_arquivo = "[DEMONSTRAÇÃO]"
    else:
        print(f"⏳ Extraindo texto do PDF: {caminho_do_arquivo}...")
        texto_para_analisar = extrair_texto_de_pdf(caminho_do_arquivo)


    if texto_para_analisar:

        # PASSO 1: ANÁLISE DE FREQUÊNCIA
        df_frequencia, total_palavras_brutas = analisar_frequencia_tematica(
            texto_para_analisar,
            palavras_a_excluir=palavras_extras_excluir,
            min_tamanho_palavra=MIN_TAMANHO_PALAVRA, # Passa o parâmetro para 'analisar_frequencia_tematica'
            top_n=top_n_palavras
        )

        print(f"✅ Análise concluída. Total de palavras brutas: {total_palavras_brutas}")

        # PASSO 2: GERAR E SALVAR RELATÓRIO
        # CHAMADA CORRIGIDA: Inclui o novo argumento
        relatorio_saida, nome_saida = gerar_relatorio_tematico(
            caminho_do_arquivo,
            df_frequencia,
            total_palavras_brutas,
            top_n_palavras,
            MIN_TAMANHO_PALAVRA # NOVO ARGUMENTO: Resolve o NameError
        )

        # IMPRIMIR O RELATÓRIO NO CONSOLE E INFORMAR O ARQUIVO
        print("\n" + relatorio_saida)

        if nome_saida:
            print("\n" + "="*70)
            print(f"SUCESSO! Relatório Temático salvo em: **{nome_saida}**")
            print("==========================================================")
    else:
        print("⚠️ O texto extraído está vazio ou a extração falhou.")