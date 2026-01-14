import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
import altair as alt

# --- SETUP DA PÁGINA (VISUAL WIDESCREEN) ---
st.set_page_config(page_title="BioFlow OS | Cloud", layout="wide", page_icon="🧬")

# --- ESTILIZAÇÃO CSS (Dark Mode Premium) ---
st.markdown("""
    <style>
    /* Cor de Fundo e Texto */
    .stApp { background-color: #0e1117; color: #fafafa; }
    
    /* Botões */
    .stButton>button { 
        background-color: #00FF7F; 
        color: black; 
        border-radius: 8px; 
        font-weight: 800; 
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #00CC66; color: white; transform: scale(1.02); }
    
    /* Métricas */
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00FF7F; }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #a0a0a0; }
    
    /* Títulos */
    h1, h2, h3 { color: #00FF7F !important; font-family: 'Helvetica Neue', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para carregar dados (com cache para performance)
def load_data():
    try:
        # Tenta ler a planilha. Se falhar, retorna vazio.
        df = conn.read(worksheet="Página1", usecols=list(range(13)), ttl=5)
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=[
            'Data', 'Peso', 'Sono', 'Energia', 'Treino', 
            'PA_Sis', 'PA_Dia', 'HRV', 'Agua_L', 
            'Dieta', 'Shot', 'Colaterais', 'Obs'
        ])

df_bio = load_data()

# --- HEADER ---
col_logo, col_title = st.columns([1, 5])
with col_title:
    st.title("BioFlow OS v6.0 [Cloud Native]")
    st.markdown("**User:** 45y • **Protocolo:** TRT + HYROX • **Status:** Conectado ao Google Drive 🟢")

st.divider()

# --- SIDEBAR (INPUT) ---
with st.sidebar:
    st.header("📝 Registro Diário")
    
    with st.form("entry_form", clear_on_submit=True):
        st.caption("Os dados vão direto para sua planilha segura.")
        
        # Grupo 1: Biometria
        st.subheader("1. Biometria & Sinais")
        input_data = st.date_input("Data", date.today(), format="DD/MM/YYYY")
        # Tenta pegar o último peso registrado
        val_peso = float(df_bio['Peso'].iloc[-1]) if not df_bio.empty and 'Peso' in df_bio.columns else 90.0
        input_peso = st.number_input("Peso (kg)", 70.0, 130.0, val_peso, step=0.1)
        
        c1, c2 = st.columns(2)
        input_pa_sis = c1.number_input("PA Sist (mmHg)", 90, 200, 120)
        input_pa_dia = c2.number_input("PA Diast (mmHg)", 50, 120, 80)
        input_hrv = st.text_input("HRV (ms)", placeholder="Ex: 48")

        # Grupo 2: Rotina
        st.subheader("2. Rotina & Treino")
        input_treino = st.multiselect("Treinos", ["Musculação", "HYROX", "LISS", "Jiu-Jitsu", "OFF"])
        input_agua = st.slider("Hidratação (Garrafas 887ml)", 0, 8, 4)
        input_dieta = st.select_slider("Adesão Dieta", ["Lixo Total", "Parcial", "Limpa 100%"])
        
        # Grupo 3: Recuperação
        st.subheader("3. Sono & Hormônios")
        input_sono = st.slider("Qualidade Sono", 0, 10, 7)
        input_energia = st.select_slider("Energia", ["Zumbi", "Baixa", "Boa", "Máquina"])
        input_shot = st.checkbox("💉 Aplicação Durateston?")
        input_colaterais = st.multiselect("Sintomas", ["Acne", "Libido Baixa", "Irritabilidade", "Retenção", "Dores"])
        
        input_obs = st.text_area("Diário de Bordo", height=100)
        
        btn_submit = st.form_submit_button("🚀 ENVIAR DADOS")
        
        if btn_submit:
            # Prepara a nova linha
            new_row = pd.DataFrame([{
                'Data': input_data.strftime("%Y-%m-%d"),
                'Peso': input_peso,
                'Sono': input_sono,
                'Energia': input_energia,
                'Treino': ", ".join(input_treino) if input_treino else "OFF",
                'PA_Sis': input_pa_sis,
                'PA_Dia': input_pa_dia,
                'HRV': input_hrv,
                'Agua_L': round(input_agua * 0.887, 2),
                'Dieta': input_dieta,
                'Shot': "SIM" if input_shot else "NÃO",
                'Colaterais': ", ".join(input_colaterais),
                'Obs': input_obs
            }])
            
            # Atualiza a planilha
            try:
                updated_df = pd.concat([df_bio, new_row], ignore_index=True)
                conn.update(worksheet="Página1", data=updated_df)
                st.success("Salvo no Google Sheets!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# --- DASHBOARD ---
tab_dash, tab_data, tab_ai = st.tabs(["📊 Dashboard Visual", "🗃️ Banco de Dados", "🤖 Relatório IA"])

with tab_dash:
    if df_bio.empty:
        st.warning("Adicione o primeiro registro na barra lateral para iniciar os gráficos.")
    else:
        # Métricas
        kp1, kp2, kp3 = st.columns(3)
        last_peso = df_bio['Peso'].iloc[-1]
        kp1.metric("Peso Atual", f"{last_peso} kg")
        kp2.metric("Última PA", f"{df_bio['PA_Sis'].iloc[-1]}/{df_bio['PA_Dia'].iloc[-1]}")
        kp3.metric("Qualidade Sono", f"{df_bio['Sono'].iloc[-1]}/10")
        
        st.divider()
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("##### 📉 Evolução de Peso")
            chart = alt.Chart(df_bio).mark_line(point=True, color='#00FF7F').encode(
                x='Data', y=alt.Y('Peso', scale=alt.Scale(zero=False)), tooltip=['Data', 'Peso']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

with tab_data:
    st.dataframe(df_bio, use_container_width=True)
    st.caption("Dados carregados diretamente do seu Google Sheets.")

with tab_ai:
    if st.button("Gerar Análise para o Coach"):
        if not df_bio.empty:
            recents = df_bio.tail(3).to_markdown()
            prompt = f"""
            [BIOFLOW DATA - LAST 3 DAYS]
            {recents}
            Solicitação: Analise tendências de sono, peso e sintomas hormonais.
            """
            st.code(prompt, language="text")
