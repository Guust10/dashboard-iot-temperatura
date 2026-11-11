import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time  # <-- Biblioteca adicionada para controlar o intervalo

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard IoT - Temperatura", page_icon="🌡️", layout="wide")

# --- URL DO FIREBASE ---
FIREBASE_URL = "https://aceu-dashboard-default-rtdb.firebaseio.com/leituras.json"

st.title("🌡️ Monitoramento de Temperatura em Tempo Real")
st.markdown("Dados capturados pelo ESP32, enviados via Serial e armazenados no Firebase.")

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
        st.error(f"Erro de conexão com o Firebase: {e}")
        return []

# --- CONTROLES DE ATUALIZAÇÃO ---
col_btn, col_auto, _ = st.columns([1, 2, 4])
with col_btn:
    if st.button("🔄 Atualizar Manualmente"):
        st.rerun()
with col_auto:
    # Checkbox para ativar/desativar o auto-refresh nativo
    auto_refresh = st.checkbox("Ativar Atualização Automática (1s)", value=True)

dados_firebase = buscar_dados()

if dados_firebase:
    df = pd.DataFrame(dados_firebase)
    
    if 'timestamp' in df.columns and 'temperatura' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
        
        ultima_temp = float(df['temperatura'].iloc[0])
        ultimo_horario = df['timestamp'].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Histórico de Leituras")
            st.write(f"**Total de registros:** {len(df)}")
            st.dataframe(df[['timestamp', 'temperatura']], use_container_width=True, height=500)
            
        with col2:
            st.subheader(f"⏱️ Última Leitura: {ultimo_horario}")
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = ultima_temp,
                title = {'text': "Temperatura (°C)"},
                gauge = {
                    'axis': {'range': [None, 50], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#538d4e"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 20], 'color': "#aaddaa"},
                        {'range': [20, 30], 'color': "#ffeb99"},
                        {'range': [30, 50], 'color': "#ff9999"}
                    ],
                }
            ))
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📈 Tendência Recente")
            df_grafico = df.head(20).iloc[::-1]
            st.line_chart(df_grafico.set_index('timestamp')['temperatura'])
            
    else:
        st.warning("O banco de dados não contém os campos esperados ('timestamp' e 'temperatura').")
else:
    st.info("Nenhum dado encontrado no Firebase. Aguardando o script enviar a primeira leitura...")

# --- LÓGICA DE ATUALIZAÇÃO AUTOMÁTICA ---
# Se o checkbox estiver marcado, o código "dorme" por 1 segundo e recomeça a execução inteira.
if auto_refresh:
    time.sleep(1)
    st.rerun()
