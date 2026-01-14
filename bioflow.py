import streamlit as st
import pandas as pd
from datetime import datetime, date

# Configuração da Página
st.set_page_config(page_title="BioFlow OS", layout="centered", page_icon="🧬")

# Estilo CSS Customizado (Clean & Dark)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #00CC66;
        color: white;
        border-radius: 10px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00994d;
        color: white;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00CC66;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧬 BioFlow OS")
st.caption("Sistema de Controle de Biohacking & Performance | v1.1 Multi-Treino")

# --- SIDEBAR (Entrada de Dados) ---
st.sidebar.header("📝 Registro Diário")
data_hoje = st.sidebar.date_input("Data", date.today())

st.sidebar.subheader("Fisiologia")
peso = st.sidebar.number_input("Peso Atual (kg)", 70.0, 130.0, 90.0, step=0.1)
sono = st.sidebar.slider("Qualidade do Sono (0-10)", 0, 10, 7)
disposicao = st.sidebar.select_slider("Nível de Energia", options=["Baixo", "Médio", "Alto", "Máximo"])

st.sidebar.subheader("Rotina")
# MUDANÇA AQUI: De selectbox para multiselect
treinos_opcoes = ["Descanso", "Musculação", "HYROX", "Cardio LISS", "Mobilidade", "Jiu-Jitsu"]
treino_feito = st.sidebar.multiselect("Treinos de Hoje", treinos_opcoes, default=["Musculação"])

agua_input = st.sidebar.number_input("Garrafas (887ml) consumidas", 0, 8, 0)
dieta_check = st.sidebar.radio("Seguiu a Dieta?", ["Sim, 100%", "Parcial", "Não (Jaquei)"])

st.sidebar.markdown("---")
if st.sidebar.button("💾 Salvar Registro (Simulação)"):
    st.sidebar.success("Dados registrados na memória temporária!")

# --- DASHBOARD (Visualização) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="⚖️ Peso", value=f"{peso} kg", delta="-0.5 kg")
with col2:
    litros = agua_input * 0.887
    st.metric(label="💧 Hidratação", value=f"{litros:.1f} L", delta=f"{agua_input}/5 Garrafas")
with col3:
    st.metric(label="💤 Sono", value=f"{sono}/10", delta="Estável")

st.divider()

# --- ÁREA DE EXPORTAÇÃO PARA IA ---
st.subheader("🤖 Exportar para o Coach (Gemini)")
st.info("Clique abaixo para gerar o relatório técnico e cole no nosso chat.")

if st.button("Gerar Relatório de Biohacking"):
    # Formata a lista de treinos para texto (ex: "Musculação, Cardio LISS")
    treinos_str = ", ".join(treino_feito) if treino_feito else "Descanso Total"
    
    prompt_ia = f"""
    [RELATÓRIO BIOFLOW OS]
    Data: {data_hoje}
    Peso: {peso}kg
    Treinos Realizados: {treinos_str}
    Sono: {sono}/10 | Energia: {disposicao}
    Hidratação: {agua_input} garrafas ({litros:.2f}L)
    Adesão à Dieta: {dieta_check}
    
    Contexto: Usuário (45 anos, 90kg) em protocolo hormonal (Durateston), foco em emagrecimento.
    Solicitação: Analise os dados acima e sugira ajustes para as próximas 24h.
    """
    st.code(prompt_ia, language="text")
    st.success("Copiado! Agora cole no chat com o Gemini.")

# --- RODAPÉ ---
st.markdown("---")
st.markdown("*Desenvolvido por nhatano | Biohacking & AI Engineering*")
