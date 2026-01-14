import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection
import altair as alt
import time
import pytz

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BioFlow Game", layout="wide", page_icon="🧬")

# --- CSS (Visual Mobile & Dark Mode) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    
    /* Botões de Água (Grandes e Fáceis de clicar) */
    div.stButton > button:first-child {
        background-color: #1E1E1E;
        color: #00FF7F;
        border: 1px solid #00FF7F;
        font-size: 24px;
        border-radius: 12px;
        height: 50px;
    }
    div.stButton > button:first-child:hover {
        background-color: #00FF7F;
        color: black;
    }
    
    /* Botão Salvar Principal (Destaque Verde) */
    .stFormSubmitButton > button {
        background-color: #00FF7F !important;
        color: black !important;
        font-weight: 800 !important;
        font-size: 18px !important;
        height: 60px !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
    }
    
    /* Ajustes de Fonte */
    h1 { font-size: 22px !important; }
    h2, h3 { color: #00FF7F !important; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # ttl=0 garante que os dados sejam baixados na hora (sem cache antigo)
        df = conn.read(worksheet="Página1", usecols=list(range(14)), ttl=0)
        return df.dropna(how="all")
    except:
        # Estrutura padrão caso a planilha esteja vazia
        return pd.DataFrame(columns=[
            'Data', 'Peso', 'Sono', 'Energia', 'Treino', 
            'PA_Sis', 'PA_Dia', 'HRV', 'Agua_L', 
            'Dieta', 'Shot', 'Colaterais', 'Obs', 'BioScore'
        ])

df_bio = load_data()

# --- LÓGICA DE GAMIFICAÇÃO (XP & NÍVEL) ---
total_logs = len(df_bio)
nivel = int(total_logs / 7) + 1 
prox_nivel = (nivel * 7) - total_logs
titulos = {1: "Novato", 2: "Iniciado", 3: "Biohacker", 4: "Otimizado", 5: "Elite", 10: "Cyborg"}
titulo_atual = titulos.get(nivel, "Lenda")

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title(f"🧬 BioFlow: Nível {nivel}")
    st.progress(min((total_logs % 7) / 7, 1.0))
    st.caption(f"Rank: **{titulo_atual}** | XP para upar: {prox_nivel} dias")

# --- LÓGICA DE ÁGUA (SESSION STATE) ---
hoje_str = date.today().strftime("%Y-%m-%d")
dados_hoje = df_bio[df_bio['Data'] == hoje_str] if not df_bio.empty else pd.DataFrame()

if 'agua_counter' not in st.session_state:
    if not dados_hoje.empty:
        try:
            litros_salvos = float(dados_hoje.iloc[0]['Agua_L'])
            st.session_state.agua_counter = int(litros_salvos / 0.887)
        except:
            st.session_state.agua_counter = 0
    else:
        st.session_state.agua_counter = 0

def add_water(): st.session_state.agua_counter += 1
def remove_water(): 
    if st.session_state.agua_counter > 0: st.session_state.agua_counter -= 1

# --- EXPANDER PRINCIPAL (Onde a mágica acontece) ---
# Fica aberto por padrão para facilitar o input rápido
with st.expander(f"📝 REGISTRO DE HOJE ({hoje_str})", expanded=True):
    
    # 1. CONTADOR DE ÁGUA (Fora do Form para ser interativo)
    st.markdown("### 💧 Hidratação")
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    with col_w1: st.button("➖", on_click=remove_water, use_container_width=True)
    with col_w3: st.button("➕", on_click=add_water, use_container_width=True)
    with col_w2:
        qtd = st.session_state.agua_counter
        litros = qtd * 0.887
        pct = min(litros / 4.0, 1.0)
        st.markdown(f"<div style='text-align:center'><b>{qtd} Garrafas</b><br><span style='color:#aaa'>{litros:.2f}L</span></div>", unsafe_allow_html=True)
        st.progress(pct)

    st.divider()

    # 2. FORMULÁRIO COMPLETO
    with st.form("game_form"):
        st.markdown("### 📊 Sinais Vitais")
        c_bio1, c_bio2 = st.columns(2)
        
        # Tenta pegar valores anteriores para facilitar
        last_peso = float(df_bio['Peso'].iloc[-1]) if not df_bio.empty and 'Peso' in df_bio.columns else 90.0
        
        peso = c_bio1.number_input("Peso (kg)", 50.0, 150.0, last_peso, step=0.1)
        sono = c_bio2.slider("Sono (Noite Passada)", 0, 10, 7)
        
        c_p1, c_p2 = st.columns(2)
        pa_sis = c_p1.number_input("PA Sistólica", 90, 200, 120)
        pa_dia = c_p2.number_input("PA Diastólica", 50, 120, 80)
        
        st.markdown("### ⚔️ Rotina & Combate")
        treino = st.multiselect("Treino", ["Musculação", "HYROX", "Cardio", "Jiu-Jitsu", "OFF"])
        dieta = st.select_slider("Dieta", ["Lixo", "Parcial", "Limpa 100%"])
        
        c_h1, c_h2 = st.columns(2)
        shot = c_h1.checkbox("💉 Shot?")
        colaterais = c_h2.multiselect("Sintomas", ["Acne", "Libido Baixa", "Irritabilidade", "Dores"])
        
        st.markdown("### 🧠 Diário de Campanha")
        obs = st.text_area("O que aconteceu agora?", placeholder="Ex: Fome intensa, Treino bom...", height=80)
        
        # CÁLCULO DO BIOSCORE (Estimativa)
        score_prev = (sono * 4) + (20 if treino and "OFF" not in treino else 0) + (30 if dieta == "Limpa 100%" else 10 if dieta == "Parcial" else -10) + (10 if litros >= 3 else 0)
        score_prev = max(0, min(100, score_prev))
        st.caption(f"Score Estimado: {score_prev}/100")

        # BOTÃO SALVAR
        submit = st.form_submit_button("💾 SALVAR / ATUALIZAR")
        
        if submit:
            # --- LÓGICA DE FUSO HORÁRIO ---
            fuso_br = pytz.timezone('America/Sao_Paulo')
            hora_atual = datetime.now(fuso_br).strftime("%H:%M")
            
            # --- LÓGICA DE DIÁRIO ACUMULATIVO ---
            obs_final = ""
            if obs: obs_final = f"[{hora_atual}] {obs}"
            
            # Recupera dados antigos se for update
            if not dados_hoje.empty:
                obs_antiga = str(dados_hoje.iloc[0]['Obs'])
                if obs_antiga != "nan" and obs_antiga != "None" and obs_antiga != "":
                    # Se escreveu algo novo, junta. Se não, mantém o velho.
                    if obs:
                        # Evita duplicar se clicar 2x
                        if obs not in obs_antiga:
                            obs_final = f"{obs_antiga} | {obs_final}"
                    else:
                        obs_final = obs_antiga
            
            # Monta a nova linha
            new_entry = pd.DataFrame([{
                'Data': hoje_str,
                'Peso': peso,
                'Sono': sono,
                'Energia': "Auto", 
                'Treino': ", ".join(treino) if treino else "OFF",
                'PA_Sis': pa_sis,
                'PA_Dia': pa_dia,
                'HRV': "-",
                'Agua_L': litros, # Pega do contador
                'Dieta': dieta,
                'Shot': "SIM" if shot else "NÃO",
                'Colaterais': ", ".join(colaterais),
                'Obs': obs_final,
                'BioScore': score_prev
            }])
            
            try:
                df_final = df_bio.copy()
                # Se já existe hoje, ATUALIZA. Se não, CRIA.
                if not df_final.empty and df_final.iloc[-1]['Data'] == hoje_str:
                    df_final.iloc[-1] = new_entry.iloc[0]
                    msg = "🔄 Dados ATUALIZADOS com sucesso!"
                else:
                    df_final = pd.concat([df_final, new_entry], ignore_index=True)
                    msg = "💾 Novo dia INICIADO!"
                
                conn.update(worksheet="Página1", data=df_final)
                st.success(f"{msg} (BioScore: {score_prev})")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# --- DASHBOARD ---
st.divider()
tab1, tab2 = st.tabs(["📈 Evolução", "🤖 Relatório IA"])

with tab1:
    if not df_bio.empty:
        # Gráfico Mobile Friendly
        chart = alt.Chart(df_bio.tail(14)).mark_area(
            line={'color':'#00FF7F'},
            color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#00FF7F', offset=0), alt.GradientStop(color='transparent', offset=1)], x1=1, x2=1, y1=1, y2=0)
        ).encode(
            x=alt.X('Data', axis=alt.Axis(format='%d/%m', labelAngle=-45)),
            y=alt.Y('Peso', scale=alt.Scale(zero=False)),
            tooltip=['Data', 'Peso', 'BioScore']
        ).properties(height=250)
        st.altair_chart(chart, use_container_width=True)

with tab2:
    if st.button("Gerar Análise para o Coach"):
        if not df_bio.empty:
            # Tenta usar tabulate se tiver, senão string normal
            try:
                recents = df_bio.tail(5).to_markdown()
            except:
                recents = df_bio.tail(5).to_string()
                
            prompt = f"""
            [BIOFLOW DATA STREAM]
            Level: {nivel} | User: 45y, TRT, HYROX.
            
            DADOS RECENTES:
            {recents}
            
            ANÁLISE SOLICITADA:
            1. Identifique padrões no BioScore (o que está derrubando a nota?).
            2. Analise a hidratação vs. Peso.
            3. Verifique os Logs de Horário no campo 'Obs' para achar janelas de fome/estresse.
            """
            st.code(prompt, language="text")
