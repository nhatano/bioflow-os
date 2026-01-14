import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
import altair as alt

# --- SETUP DA PÁGINA ---
# Mantemos wide para o desktop, mas o layout abaixo se adapta ao mobile
st.set_page_config(page_title="BioFlow Mobile", layout="wide", page_icon="🧬")

# --- CSS PARA MOBILE ---
st.markdown("""
    <style>
    /* Ajustes para telas pequenas */
    .stApp { background-color: #0e1117; color: #fafafa; }
    
    /* Botão de envio gigante e fácil de clicar no celular */
    .stButton>button { 
        width: 100%;
        height: 60px;
        background-color: #00FF7F; 
        color: black; 
        border-radius: 12px; 
        font-size: 18px;
        font-weight: 800; 
        border: none;
    }
    
    /* Melhorar visualização dos inputs */
    .stNumberInput input { font-size: 18px; }
    
    /* Títulos */
    h1 { font-size: 24px !important; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Página1", usecols=list(range(13)), ttl=5)
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=[
            'Data', 'Peso', 'Sono', 'Energia', 'Treino', 
            'PA_Sis', 'PA_Dia', 'HRV', 'Agua_L', 
            'Dieta', 'Shot', 'Colaterais', 'Obs'
        ])

df_bio = load_data()

# --- CABEÇALHO ---
st.title("🧬 BioFlow Mobile")
st.caption("Protocolo TRT + HYROX | User: 45y")

# --- ÁREA DE REGISTRO (AGORA NO CORPO PRINCIPAL, NÃO SIDEBAR) ---
# Usamos um expander que fica fechado para não poluir, e abre fácil no dedo
with st.expander("📝 TOQUE AQUI PARA ADICIONAR REGISTRO", expanded=False):
    
    with st.form("entry_form", clear_on_submit=True):
        st.markdown("### 1. Sinais Vitais")
        d_col1, d_col2 = st.columns(2)
        input_data = d_col1.date_input("Data", date.today(), format="DD/MM/YYYY")
        
        # Pega último peso
        val_peso = float(df_bio['Peso'].iloc[-1]) if not df_bio.empty and 'Peso' in df_bio.columns else 90.0
        input_peso = d_col2.number_input("Peso (kg)", 70.0, 130.0, val_peso, step=0.1)
        
        p_col1, p_col2, p_col3 = st.columns(3)
        input_pa_sis = p_col1.number_input("Sistólica", 90, 200, 120)
        input_pa_dia = p_col2.number_input("Diastólica", 50, 120, 80)
        input_hrv = p_col3.text_input("HRV", placeholder="ms")

        st.markdown("### 2. Rotina")
        input_treino = st.multiselect("Treino", ["Musculação", "HYROX", "LISS", "Jiu-Jitsu", "OFF"])
        input_agua = st.slider("Água (Garrafas 887ml)", 0, 8, 4)
        input_dieta = st.select_slider("Dieta", ["Lixo", "Parcial", "100%"])
        
        st.markdown("### 3. Recuperação")
        input_sono = st.slider("Sono (0-10)", 0, 10, 7)
        input_energia = st.select_slider("Energia", ["Zumbi", "Baixa", "Boa", "Top"])
        
        c_col1, c_col2 = st.columns([1, 2])
        input_shot = c_col1.checkbox("💉 Shot?")
        input_colaterais = c_col2.multiselect("Sintomas", ["Acne", "Libido Baixa", "Irritabilidade", "Dores"])
        
        input_obs = st.text_area("Obs:", height=80)
        
        # Botão Grande Verde
        btn_submit = st.form_submit_button("💾 SALVAR DADOS")
        
        if btn_submit:
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
            
            try:
                updated_df = pd.concat([df_bio, new_row], ignore_index=True)
                conn.update(worksheet="Página1", data=updated_df)
                st.success("✅ Salvo!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

st.divider()

# --- VISUALIZAÇÃO DE DADOS (ABAIXO DO FORMULÁRIO) ---
tab_dash, tab_ai = st.tabs(["📊 Gráficos", "🤖 IA Coach"])

with tab_dash:
    if not df_bio.empty:
        # Métricas em Cards (Ficam empilhados no celular automaticamente)
        k1, k2, k3 = st.columns(3)
        last = df_bio.iloc[-1]
        k1.metric("Peso", f"{last['Peso']}kg")
        k2.metric("Sono", f"{last['Sono']}/10")
        k3.metric("PA", f"{last['PA_Sis']}/{last['PA_Dia']}")
        
        st.caption("Gire o celular para ver melhor os gráficos")
        
        # Gráfico Simplificado para Mobile
        chart = alt.Chart(df_bio).mark_area(
            line={'color':'#00FF7F'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#00FF7F', offset=0),
                       alt.GradientStop(color='rgba(0, 255, 127, 0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('Data', axis=alt.Axis(format='%d/%m', labelAngle=-45)),
            y=alt.Y('Peso', scale=alt.Scale(zero=False)),
            tooltip=['Data', 'Peso', 'Treino']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
        
        # Tabela compacta (mostra só o essencial no mobile)
        st.markdown("#### 🗓️ Últimos Registros")
        st.dataframe(
            df_bio[['Data', 'Peso', 'Treino', 'Dieta']].sort_values(by='Data', ascending=False).head(5),
            hide_index=True,
            use_container_width=True
        )

with tab_ai:
    if st.button("Gerar Análise IA"):
        if not df_bio.empty:
            # Usando to_string para evitar dependência do tabulate se der erro, 
            # ou mantendo to_markdown se tabulate estiver instalado
            try:
                recents = df_bio.tail(4).to_markdown()
            except:
                recents = df_bio.tail(4).to_string()
                
            prompt = f"""
            [BIOFLOW MOBILE DATA]
            {recents}
            Solicitação: Analise tendências curtas de peso x sono x hormônios.
            """
            st.code(prompt, language="text")
