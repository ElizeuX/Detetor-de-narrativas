import pandas as pd
from pypdf import PdfReader
import re
import os
from datetime import datetime
from collections import Counter, defaultdict

# --- FUNÇÕES DE EXTRAÇÃO (Reutilizadas) ---

def extrair_texto_de_pdf(caminho_arquivo):
    """Lê o PDF no caminho especificado e retorna todo o seu conteúdo como texto."""
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

# --- FUNÇÃO PRINCIPAL: ANÁLISE DE DIÁLOGOS E INTERAÇÕES ---

def analisar_distribuicao(texto, janela_interacao=50, min_tamanho_nome=4):
    """
    Analisa a distribuição de diálogos e interações entre personagens.
    """
    if not texto:
        return pd.DataFrame(), pd.DataFrame(), []

    texto_limpo = texto.replace('\n', ' ')

    # Heurística para encontrar nomes próprios: palavras capitalizadas com min_tamanho
    # Simplificado: Palavras que começam com maiúscula e têm 4+ caracteres.
    nomes_possiveis = set(re.findall(r'\b[A-Z][a-záéíóúàèìòùâêîôûãõç]{3,}\b', texto_limpo))

    # 1. Contagem de Diálogos
    contagem_dialogo = Counter()

    # Expressão regular complexa para capturar falas (entre aspas) e o nome do falante
    # Procura por: [Palavra Capitalizada com 4+ letras] + (algumas palavras) + "FALA"
    dialogos_encontrados = re.findall(
        r'(\b[A-Z][a-záéíóúàèìòùâêîôûãõç]{3,}\b)(?:\s\w+){0,5}?\s*(?:"([^"]+)")',
        texto_limpo
    )

    for nome_bruto, fala in dialogos_encontrados:
        # Filtra pelo conjunto de nomes possíveis para evitar falsos positivos
        if nome_bruto in nomes_possiveis:
            contagem_dialogo[nome_bruto] += 1

    # 2. Contagem de Interações (Proximidade)
    interacoes = defaultdict(int)
    palavras = texto_limpo.split()

    # Filtra as palavras para deixar apenas os nomes possíveis
    nomes_no_texto = [(i, palavra) for i, palavra in enumerate(palavras) if palavra in nomes_possiveis]

    for i in range(len(nomes_no_texto)):
        idx_a, nome_a = nomes_no_texto[i]

        # Compara com os nomes subsequentes dentro da janela de interação
        for j in range(i + 1, len(nomes_no_texto)):
            idx_b, nome_b = nomes_no_texto[j]

            # Se a distância entre os nomes (em palavras) for menor que a janela
            if idx_b - idx_a <= janela_interacao:
                # Cria uma chave canônica (sempre alfabética) para o par
                par = tuple(sorted((nome_a, nome_b)))
                if par[0] != par[1]: # Ignora auto-interação
                    interacoes[par] += 1
            else:
                # Se o nome já estiver fora da janela, podemos quebrar o loop interno
                break

    # 3. Preparação dos DataFrames
    df_dialogo = pd.DataFrame(contagem_dialogo.most_common(), columns=['Personagem', 'Nº de Falas'])

    # Conversão de Interações para DataFrame
    df_interacoes = pd.DataFrame(
        [(f"{p[0]} e {p[1]}", count) for p, count in interacoes.items()],
        columns=['Par de Personagens', 'Frequência de Interação']
    ).sort_values(by='Frequência de Interação', ascending=False)

    return df_dialogo, df_interacoes, list(nomes_possiveis)

# --- 3. FUNÇÃO GERAR RELATÓRIO ---

def gerar_relatorio_dialogo(caminho_arquivo, df_dialogo, df_interacoes, nomes_identificados, janela_interacao):
    """Gera o relatório formatado e salva em um arquivo de texto."""
    nome_saida = "relatorio_dialogo_interacao.txt"

    relatorio = "=========================================================\n"
    relatorio += "| RELATÓRIO DE DISTRIBUIÇÃO DE DIÁLOGOS E INTERAÇÕES |\n"
    relatorio += "=========================================================\n"
    relatorio += f"Data da Análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    relatorio += f"Arquivo Fonte: {caminho_arquivo}\n"
    relatorio += f"Janela de Proximidade para Interação: {janela_interacao} palavras\n"
    relatorio += f"Nomes Próprios Possíveis Identificados ({len(nomes_identificados)}): {', '.join(sorted(nomes_identificados))}\n\n"

    # 1. Distribuição de Diálogos
    relatorio += "### 1. DISTRIBUIÇÃO DE DIÁLOGOS (Tempo de Fala)\n"
    if df_dialogo.empty:
        relatorio += "⚠️ Nenhuma fala (texto entre aspas) foi detectada ou associada a um personagem.\n"
    else:
        relatorio += df_dialogo.to_string(index=False)
    relatorio += "\n\n"

    # 2. Frequência de Interações
    relatorio += "### 2. FREQUÊNCIA DE INTERAÇÕES (Conexões Mais Fortes)\n"
    if df_interacoes.empty:
        relatorio += "⚠️ Nenhuma interação significativa foi detectada na janela de proximidade.\n"
    else:
        relatorio += "Métrica: Quantas vezes os personagens apareceram a menos de 50 palavras de distância.\n"
        relatorio += df_interacoes.head(15).to_string(index=False) # Top 15 Interações
    relatorio += "\n"

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
    JANELA_INTERACAO = 50 # Distância máxima de palavras para contar como interação

    print(f"--- 👥 Analisador de Diálogos e Interações ---")

    if not os.path.exists(caminho_do_arquivo):
        print(f"❌ Erro: Arquivo '{caminho_do_arquivo}' não encontrado. Usando texto de demonstração.")
        # Texto de demonstração com diálogos e interações
        texto_para_analisar = """
        Kaelin estava na taverna. Ele viu Alara. "Vamos sair daqui," disse Kaelin.
        (Muitas palavras de descrição e ação)
        Alara concordou e pediu que o anão, Brynn, os acompanhasse. "Você vem, Brynn?" perguntou Alara.
        Brynn respondeu: "Claro, Alara. O Kaelin precisa de proteção."
        Kaelin e Alara se entreolharam. O mago Xylar apareceu, mas não disse nada.
        Brynn e Kaelin seguiram, enquanto Xylar observava.
        """ * 10
        caminho_do_arquivo = "[DEMONSTRAÇÃO]"
    else:
        print(f"⏳ Extraindo texto do PDF: {caminho_do_arquivo}...")
        texto_para_analisar = extrair_texto_de_pdf(caminho_do_arquivo)


    if texto_para_analisar:

        # PASSO 1: ANÁLISE
        df_dialogo, df_interacoes, nomes_identificados = analisar_distribuicao(
            texto_para_analisar,
            janela_interacao=JANELA_INTERACAO
        )

        print(f"✅ Análise concluída.")

        # PASSO 2: GERAR E SALVAR RELATÓRIO
        relatorio_saida, nome_saida = gerar_relatorio_dialogo(
            caminho_do_arquivo,
            df_dialogo,
            df_interacoes,
            nomes_identificados,
            JANELA_INTERACAO
        )

        # IMPRIMIR O RELATÓRIO NO CONSOLE E INFORMAR O ARQUIVO
        print("\n" + relatorio_saida)

        if nome_saida:
            print("\n" + "="*70)
            print(f"SUCESSO! Relatório de Diálogos e Interações salvo em: **{nome_saida}**")
            print("==========================================================")
    else:
        print("⚠️ O texto extraído está vazio ou a extração falhou.")