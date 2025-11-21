import pandas as pd
from pypdf import PdfReader
import re
import os
from datetime import datetime

# --- 1. LISTA DE MULETAS E VÍCIOS DE LINGUAGEM ---
# Adicione ou remova termos conforme a necessidade do seu idioma (Português/BR)
LISTA_VICIOS = [
    "tipo assim", "né", "tá ligado", "a nível de", "enfim",
    "entendeu", "de repente", "aí", "daí", "e daí", "e tal",
    "aliás", "no caso", "na verdade", "inclusive", "digamos assim",
    "em termos de", "eu acho que", "praticamente", "literalmente",
    "bem", "realmente", "basicamente", "com certeza", "em suma"
]

# --- FUNÇÕES DE EXTRAÇÃO E CONTAGEM ---

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

def contar_muletas(texto, lista_muletas, tamanho_janela=1000):
    """
    Processa o texto, conta a ocorrência de cada muleta/vício e
    analisa a frequência por janela de palavras.
    """
    if not texto:
        return pd.DataFrame(), pd.DataFrame()

    texto_normalizado = texto.lower()
    palavras = texto_normalizado.replace('\n', ' ').split()
    total_palavras = len(palavras)

    # 1. Contagem Geral (Frequência Absoluta e Relativa)
    contagem_geral = {}
    total_muletas_contadas = 0

    for muleta in lista_muletas:
        # Usa regex para encontrar a muleta como palavra/frase completa (\b)
        padrao = r'\b' + re.escape(muleta) + r'\b'
        ocorrencias = len(re.findall(padrao, texto_normalizado))
        contagem_geral[muleta] = ocorrencias
        total_muletas_contadas += ocorrencias

    df_geral = pd.DataFrame(list(contagem_geral.items()), columns=['Muleta/Vício', 'Ocorrências'])
    df_geral['Frequência Relativa (%)'] = (df_geral['Ocorrências'] / total_muletas_contadas * 100).round(2) if total_muletas_contadas > 0 else 0
    df_geral = df_geral.sort_values(by='Ocorrências', ascending=False)

    # 2. Contagem por Janela (Para distribuição)
    dados_janela = []

    for i in range(0, total_palavras, tamanho_janela):
        janela_palavras = palavras[i:i + tamanho_janela]
        janela_texto = " ".join(janela_palavras)
        contagem_janela = 0

        for muleta in lista_muletas:
            padrao = r'\b' + re.escape(muleta) + r'\b'
            contagem_janela += len(re.findall(padrao, janela_texto))

        dados_janela.append({
            'janela': i // tamanho_janela,
            # A coluna 'inicio_palavra' é desnecessária aqui e foi removida para simplificar
            'total_muletas_na_janela': contagem_janela,
            'frequencia_por_1000_palavras': (contagem_janela / len(janela_palavras)) * 1000 if len(janela_palavras) > 0 else 0
        })

    df_janela = pd.DataFrame(dados_janela)

    return df_geral, df_janela

# --- 2. FUNÇÃO GERAR RELATÓRIO (CORRIGIDA) ---

def gerar_relatorio(caminho_arquivo, total_palavras, df_geral, df_janela, tamanho_janela_configurado):
    """
    Gera uma string de relatório formatada e a salva em um arquivo de texto.
    """
    total_muletas = df_geral['Ocorrências'].sum()

    # Inicia a string do relatório
    relatorio = "=================================================\n"
    relatorio += f"| RELATÓRIO DE ANÁLISE DE VÍCIOS DE LINGUAGEM |\n"
    relatorio += "=================================================\n"
    relatorio += f"Data da Análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    relatorio += f"Arquivo Fonte: {caminho_arquivo}\n"
    relatorio += f"Total de Palavras no Texto: {total_palavras}\n"
    relatorio += "\n--- RESUMO GERAL ---\n"
    relatorio += f"Total de Muletas/Vícios Encontrados: {total_muletas}\n"
    if total_palavras > 0:
        relatorio += f"Frequência Geral (Proporção por Palavra): {(total_muletas / total_palavras * 100):.2f}%\n"
    relatorio += "\n"

    # Adiciona a tabela de resultados gerais
    relatorio += "### 1. OCORRÊNCIAS POR TIPO DE MULETA\n"
    relatorio += df_geral.to_string(index=False)
    relatorio += "\n\n"

    # Adiciona a tabela de distribuição por janela
    relatorio += "### 2. DISTRIBUIÇÃO AO LONGO DO TEXTO (Frequência por Janela)\n"

    # CORREÇÃO APLICADA: Usa o parâmetro 'tamanho_janela_configurado' (valor de 1000, por exemplo)
    relatorio += f"Tamanho da Janela: {tamanho_janela_configurado} palavras\n"
    relatorio += df_janela.to_string(index=False)
    relatorio += "\n"

    # Salvar o relatório em arquivo
    nome_saida = "relatorio_vicios.txt"
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
    tamanho_janela = 1000  # <--- Variável usada na CORREÇÃO

    print(f"--- 📝 Contador de Muletas e Vícios de Linguagem ---")

    if not os.path.exists(caminho_do_arquivo):
        print(f"❌ Erro: Arquivo '{caminho_do_arquivo}' não encontrado. Usando texto de demonstração.")
        # Texto de demonstração
        texto_para_analisar = ("eu acho que tipo assim, o texto tá bom né. Aí, de repente, no caso, a gente pode mudar o final. Inclusive, eu acho que tá ligado?").lower() * 20
        caminho_do_arquivo = "[DEMONSTRAÇÃO]"
    else:
        print(f"⏳ Extraindo texto do PDF: {caminho_do_arquivo}...")
        texto_para_analisar = extrair_texto_de_pdf(caminho_do_arquivo)


    if texto_para_analisar and len(texto_para_analisar.split()) > 0:
        total_palavras = len(texto_para_analisar.split())
        print(f"✅ Texto pronto. Total de palavras: {total_palavras}")

        # CONTAR AS MULETAS
        df_geral, df_janela = contar_muletas(texto_para_analisar, LISTA_VICIOS, tamanho_janela)

        if not df_geral.empty:
            # CHAMADA CORRIGIDA: Passa 'tamanho_janela' como argumento
            relatorio_saida, nome_saida = gerar_relatorio(caminho_do_arquivo, total_palavras, df_geral, df_janela, tamanho_janela)

            # IMPRIMIR O RELATÓRIO NO CONSOLE E INFORMAR O ARQUIVO
            print("\n" + relatorio_saida)

            if nome_saida:
                print("\n" + "="*50)
                print(f"SUCESSO! Relatório completo salvo em: **{nome_saida}**")
                print("=================================================")
        else:
            print("Não foi possível gerar o relatório (dados de contagem vazios).")
    else:
        print("⚠️ O texto extraído está vazio ou a extração falhou.")