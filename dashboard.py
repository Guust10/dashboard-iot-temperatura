import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
# Mudei o layout para wide e reduzi o menu padrão para um visual mais limpo
st.set_page_config(page_title="Dashboard Monitoramento - ACEU", page_icon="🌡️", layout="wide", initial_sidebar_state="collapsed")

# --- INJEÇÃO DE CSS PARA CABER EM UMA TELA (SEM ROLAGEM) ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            max-width: 95%;
        }
        /* Reduz o espaço entre os elementos */
        div[data-testid="stVerticalBlock"] > div {
            padding-bottom: 0.2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- URL DO FIREBASE ---
FIREBASE_URL = "https://aceu-dashboard-default-rtdb.firebaseio.com/leituras.json"

# --- CABEÇALHO (LOGO + NOMES) ---
col_logo, col_texto = st.columns([1, 5])

with col_logo:
    # O Streamlit vai procurar a imagem na mesma pasta do script
    try:
        st.image("unesp_logo.png", use_container_width=True)
    except:
        # Caso a imagem não esteja na pasta, mostra um aviso discreto
        st.info("⚠️ Imagem 'unesp_logo.png' não encontrada na pasta.")

with col_texto:
    st.markdown("<h2 style='margin-bottom: 0rem; padding-bottom: 0rem;'>ACEU 6 - Monitoramento Ambiental</h2>", unsafe_allow_html=True)
    # Lista de integrantes extraída da imagem e combinada com o seu nome
    integrantes = "Gustavo da Costa Lilli, Thiago Mizael de Vasconcelos, Icaro Hideki Otino de Almeida, Enzo Oliveira da Rocha Ragassi Cruz, Renan Yoshimoto Wako, Jose Claudio Pereira Ramos Filho, Lucas Nunes Feuser, Leonardo Blaya Biffe, Thalys Canevaroli e Marcelo Renato Araujo Filho."
    st.markdown(f"<p style='color: #aaaaaa; font-size: 14px;'><strong>Integrantes:</strong> {integrantes}</p>", unsafe_allow_html=True)

st.markdown("---") # Linha divisória

# --- FUNÇÃO PARA BUSCAR DADOS ---
def buscar_dados():
    try:
        resposta = requests.get(FIREBASE_URL)
        if resposta.status_code == 200 and resposta.json() is not None:
            dados = resposta.json()
            lista_dados = []
            for chave, valor in dados.items():
                valor['id'] = chave
                lista_dados.append(valor)
            return lista_dados
        return []
    except Exception as e:
        return []

# --- CONTROLES DE ATUALIZAÇÃO ---
col_btn, col_auto, _ = st.columns([1.5, 2.5, 6])
with col_btn:
    if st.button("🔄 Atualizar Manualmente", use_container_width=True):
        st.rerun()
with col_auto:
    auto_refresh = st.checkbox("Atualização Automática (1s)", value=True)

dados_firebase = buscar_dados()

if dados_firebase:
    df = pd.DataFrame(dados_firebase)
    
    if 'timestamp' in df.columns and 'temperatura' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
        
        ultima_temp = float(df['temperatura'].iloc[0])
        ultimo_horario = df['timestamp'].iloc[0]
        
        # --- DIVISÃO PRINCIPAL DA TELA (ESQUERDA / DIREITA) ---
        col_esq, col_dir = st.columns([1, 1.2]) # Coluna direita ligeiramente maior para os gráficos
        
        with col_esq:
            st.markdown("#### 📋 Histórico de Leituras")
            # A altura foi travada em ~480px para não estourar o fundo da tela
            st.dataframe(df[['timestamp', 'temperatura']], use_container_width=True, height=480)
            
        with col_dir:
            st.markdown(f"#### ⏱️ Tempo Real (Última: {ultimo_horario})")
            
            # 1. GRÁFICO GAUGE (VELOCÍMETRO) - AJUSTADO PARA 25 a 35 Graus
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = ultima_temp,
                number = {'suffix': " °C", 'font': {'size': 40}},
                gauge = {
                    'axis': {'range': [25, 35], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#2b2b2b"}, # Cor do ponteiro
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [25, 28], 'color': "#aaddaa"}, # Verde (Frio/Agradável)
                        {'range': [28, 32], 'color': "#ffeb99"}, # Amarelo (Morno)
                        {'range': [32, 35], 'color': "#ff9999"}  # Vermelho (Quente)
                    ],
                }
            ))
            # Margens apertadas e altura fixa para caber na tela
            fig_gauge.update_layout(height=230, margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # 2. GRÁFICO DE LINHA (PLOTLY) - AJUSTADO PARA 25 a 35 Graus
            df_grafico = df.head(15).iloc[::-1] # Últimas 15 leituras para não poluir
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df_grafico['timestamp'], 
                y=df_grafico['temperatura'], 
                mode='lines+markers',
                line=dict(color='#538d4e', width=3),
                marker=dict(size=8, color='#3a3a3c')
            ))
            
            fig_line.update_layout(
                height=230, 
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis=dict(range=[24, 36], title="Temperatura (°C)"), # Eixo Y travado próximo ao range 25-35
                xaxis=dict(showticklabels=False), # Oculta os textos de data no eixo X para economizar espaço vertical
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            # Adiciona grades horizontais leves
            fig_line.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
            st.plotly_chart(fig_line, use_container_width=True)
            
else:
    st.info("Nenhum dado encontrado no Firebase. Aguardando o script enviar a primeira leitura...")

# Lógica de atualização automática
if auto_refresh:
    time.sleep(1)
    st.rerun()
