import nltk
import pandas as pd
import matplotlib.pyplot as plt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from pypdf import PdfReader # Para extrair texto de PDFs
import os # Para verificar a existência do arquivo

# Inicializa o analisador VADER (Valence Aware Dictionary and sEntiment Reasoner)
# Certifique-se de que 'vader_lexicon' foi baixado: nltk.download('vader_lexicon')
try:
    sia = SentimentIntensityAnalyzer()
except LookupError:
    # Se o download não foi feito, tenta fazer
    print("Baixando 'vader_lexicon' do NLTK...")
    nltk.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()


def extrair_texto_de_pdf(caminho_arquivo):
    """
    Lê o PDF e retorna todo o seu conteúdo como uma única string de texto.
    """
    texto_completo = ""
    try:
        reader = PdfReader(caminho_arquivo)

        # Itera sobre todas as páginas e extrai o texto
        for page in reader.pages:
            # Usa .extract_text() para obter o conteúdo textual da página
            texto_completo += page.extract_text() + "\n"

        return texto_completo
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo não encontrado no caminho: {caminho_arquivo}")
        return None
    except Exception as e:
        print(f"❌ Ocorreu um erro durante a leitura do PDF: {e}")
        return None


def dividir_e_analisar(texto, tamanho_janela=1000):
    """
    Divide o texto em janelas (chunks) e calcula a pontuação de sentimento
    composta (compound score) para cada janela.
    """
    if not texto or len(texto.strip()) < tamanho_janela:
        print("⚠️ Texto muito curto para análise ou vazio.")
        return pd.DataFrame()

    # Remove quebras de linha, espaços extras e divide em palavras
    palavras = texto.replace('\n', ' ').split()

    pontuacoes = []

    # Itera sobre o texto em janelas de tamanho fixo
    for i in range(0, len(palavras), tamanho_janela):
        janela = " ".join(palavras[i:i + tamanho_janela])

        # Analisa o sentimento da janela
        sentimento = sia.polarity_scores(janela)

        # Armazena a pontuação composta e a posição
        pontuacoes.append({
            'janela': i // tamanho_janela,
            'inicio_palavra': i,
            'pontuacao_composta': sentimento['compound']
        })

    return pd.DataFrame(pontuacoes)


def detectar_pontos_de_virada(df_pontuacoes, limite_mudanca=0.4):
    """
    Identifica "pontos de virada" detectando mudanças abruptas (maiores que o limite)
    na pontuação de sentimento composta.
    """
    if df_pontuacoes.empty:
        return pd.DataFrame()

    df = df_pontuacoes.copy()

    # Calcula a diferença absoluta da pontuação de sentimento entre janelas adjacentes
    df['mudanca'] = df['pontuacao_composta'].diff().abs()

    # Define os pontos de virada onde a mudança excede um limite
    pontos_virada = df[df['mudanca'] > limite_mudanca].copy()

    # Ajusta o índice para apontar para o início da *nova* seção (a janela após a mudança)
    pontos_virada.index = pontos_virada.index - 1

    # Pega a pontuação da janela onde a virada *aconteceu* (a janela de destino)
    pontos_virada['pontuacao_no_ponto_virada'] = df['pontuacao_composta'].shift(-1).iloc[pontos_virada.index]

    return pontos_virada.dropna(subset=['pontuacao_no_ponto_virada'])


def visualizar_narrativa(df_pontuacoes, pontos_virada):
    """
    Gera um gráfico da Pontuação de Sentimento ao longo da história,
    destacando os pontos de virada detectados.
    """
    plt.figure(figsize=(12, 6))

    # Curva de Sentimento
    plt.plot(df_pontuacoes['janela'], df_pontuacoes['pontuacao_composta'],
             label='Sentimento Composto', color='darkblue', marker='o', markersize=4)

    # Pontos de Virada
    if not pontos_virada.empty:
        # Usa o índice da janela + 1 (pois a mudança foi detectada no início da próxima janela)
        virada_indices = pontos_virada['janela'] + 1

        plt.scatter(virada_indices, pontos_virada['pontuacao_no_ponto_virada'],
                    color='red', s=150, zorder=5, label='Ponto de Virada Detectado', marker='X')

        for idx, row in pontos_virada.iterrows():
            # Adiciona anotação
            plt.annotate(f"Virada! ({row['mudanca']:.2f})",
                         (row['janela'] + 1, row['pontuacao_no_ponto_virada']),
                         textcoords="offset points", xytext=(0,15), ha='center',
                         fontsize=10, color='red', weight='bold')

    plt.title('Curva de Sentimento da Narrativa e Pontos de Virada', fontsize=16)
    plt.xlabel(f'Janela de Texto (Unidades de {len(df_pontuacoes.index) * df_pontuacoes["inicio_palavra"].diff().iloc[1] if not df_pontuacoes.empty and df_pontuacoes["inicio_palavra"].diff().iloc[1] else 1000} Palavras)', fontsize=12)
    plt.ylabel('Pontuação de Sentimento Composto (VADER) [-1.0 a +1.0]', fontsize=12)
    plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.5) # Linha Neutra
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.show()

# --- Bloco Principal de Execução ---
if __name__ == "__main__":

    # 📌 CONFIGURAÇÕES
    # Coloque o caminho para o seu arquivo PDF
    # Se não tiver um PDF, use o texto de exemplo (removendo o '#')
    caminho_do_arquivo = 'main.pdf'
    tamanho_janela = 1000  # Quantidade de palavras por bloco de análise
    limite_mudanca = 0.4   # Limiar para detectar uma mudança abrupta no tom (Ponto de Virada)

    # EXEMPLO DE TEXTO (Para teste se não tiver um PDF)
    if not os.path.exists(caminho_do_arquivo) or not caminho_do_arquivo.endswith('.pdf'):
        print("\n⚠️ Usando texto de demonstração, pois o PDF não foi encontrado ou não está configurado.")
        texto_para_analisar = """
        A vida era perfeita, um mar de tranquilidade e felicidade imensa. O sentimento
        era de paz total, alegria e harmonia por longas páginas, com pontuação
        de sentimento próxima a +1.0. A história focava em festividades e bondade.
        (Repita este bloco de texto positivo umas 10 vezes para simular um Ato I longo).
        """ * 10 + """
        ENTRETANTO, a tragédia atingiu o reino. O desespero se instalou,
        a guerra começou, e o herói perdeu tudo o que amava. Um momento de dor
        e sofrimento terrível. O tom se torna abruptamente negativo, caindo para -1.0.
        Este é o Incidente Incitante, uma grande virada. A partir daqui, a tensão é alta.
        (Repita este bloco de texto negativo umas 10 vezes para simular a Queda).
        """ * 10 + """
        Após meses de luta e grande sacrifício, o herói encontra uma faísca
        de esperança. A jornada recomeça, a determinação é renovada, e a vitória,
        embora difícil, parece possível. O sentimento sobe um pouco, indicando
        resolução, mas não felicidade completa.
        """ * 5
    else:
        # PASSO 1: EXTRAIR O TEXTO DO PDF
        print(f"⏳ Extraindo texto do PDF: {caminho_do_arquivo}...")
        texto_para_analisar = extrair_texto_de_pdf(caminho_do_arquivo)


    if texto_para_analisar:
        print(f"✅ Texto pronto. Total de {len(texto_para_analisar.split())} palavras para análise.")

        # PASSO 2: ANALISAR O SENTIMENTO POR JANELA
        df_resultado = dividir_e_analisar(texto_para_analisar, tamanho_janela=tamanho_janela)

        if df_resultado.empty:
            print("Não há dados suficientes para prosseguir com a análise.")
        else:
            print("\n--- Resultados da Análise de Sentimento por Janela (Amostra) ---")
            print(df_resultado.head())

            # PASSO 3: DETECTAR PONTOS DE VIRADA
            df_viradas = detectar_pontos_de_virada(df_resultado, limite_mudanca=limite_mudanca)

            print("\n--- Pontos de Virada Detectados ---")
            if not df_viradas.empty:
                print(df_viradas[['janela', 'mudanca', 'pontuacao_no_ponto_virada']])
                print(f"\n✨ Pontos de Virada (Janela que inicia a mudança): {list(df_viradas['janela'] + 1)}")

                # PASSO 4: VISUALIZAR A NARRATIVA
                visualizar_narrativa(df_resultado, df_viradas)
            else:
                print(f"Nenhum ponto de virada abrupto detectado (Limite: >{limite_mudanca}). Tente reduzir o limite ou aumentar o tamanho da janela.")