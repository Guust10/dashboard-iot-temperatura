import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard IoT - Temperatura", page_icon="🌡️", layout="wide")

# --- URL DO FIREBASE ---
# Substitua pela URL do seu Firebase Realtime Database
# IMPORTANTE: Mantenha o ".json" no final!
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
            # O Firebase salva os dados com chaves únicas geradas automaticamente
            for chave, valor in dados.items():
                valor['id'] = chave
                lista_dados.append(valor)
            return lista_dados
        return []
    except Exception as e:
        st.error(f"Erro de conexão com o Firebase: {e}")
        return []

# Botão de atualização manual
col_btn, _ = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Atualizar Dados"):
        st.rerun()

dados_firebase = buscar_dados()

if dados_firebase:
    # Converter para DataFrame do Pandas para facilitar a manipulação
    df = pd.DataFrame(dados_firebase)
    
    # Garante que as colunas existem
    if 'timestamp' in df.columns and 'temperatura' in df.columns:
        # Organiza da leitura mais nova para a mais velha (baseado no texto do timestamp ou id)
        df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
        
        # Pega a última leitura (a primeira da lista após ordenar)
        ultima_temp = float(df['temperatura'].iloc[0])
        ultimo_horario = df['timestamp'].iloc[0]
        
        # --- DIVISÃO DA TELA (COLUNA ESQUERDA E DIREITA) ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Histórico de Leituras")
            st.write(f"**Total de registros:** {len(df)}")
            
            # Mostra a tabela formatada
            # Selecionamos apenas as colunas que importam para visualização
            st.dataframe(df[['timestamp', 'temperatura']], use_container_width=True, height=500)
            
        with col2:
            st.subheader(f"⏱️ Última Leitura: {ultimo_horario}")
            
            # --- GRÁFICO DE VELOCÍMETRO (GAUGE) ---
            # Exatamente como na referência do Ubidots
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = ultima_temp,
                title = {'text': "Temperatura (°C)"},
                gauge = {
                    'axis': {'range': [None, 50], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#538d4e"}, # Cor do Termo para manter a identidade visual!
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 20], 'color': "#aaddaa"}, # Frio (verde claro)
                        {'range': [20, 30], 'color': "#ffeb99"}, # Agradável (amarelo)
                        {'range': [30, 50], 'color': "#ff9999"}  # Quente (vermelho claro)
                    ],
                }
            ))
            # Ajuste de layout para caber perfeitamente na coluna
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # --- BÔNUS: GRÁFICO DE LINHA (TENDÊNCIA) ---
            st.subheader("📈 Tendência Recente")
            # Pegar os últimos 20 registros para o gráfico de linha e inverter para ordem cronológica
            df_grafico = df.head(20).iloc[::-1]
            st.line_chart(df_grafico.set_index('timestamp')['temperatura'])
            
    else:
        st.warning("O banco de dados não contém os campos esperados ('timestamp' e 'temperatura').")
else:
    st.info("Nenhum dado encontrado no Firebase. Aguardando o script enviar a primeira leitura...")
