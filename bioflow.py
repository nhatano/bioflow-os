import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection
import altair as alt
import time

# --- SETUP ---
st.set_page_config(page_title="BioFlow Game", layout="wide", page_icon="🧬")

# --- CSS (Visual de Game) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    
    /* Botões de Ação (Água) */
    div.stButton > button:first-child {
        background-color: #1E1E1E;
        color: #00FF7F;
        border: 1px solid #00FF7F;
        font-size: 20px;
        border-radius: 10px;
    }
    div.stButton > button:first-child:hover {
        background-color: #00FF7F;
        color: black;
    }
    
    /* Botão Salvar Principal (Destaque) */
    .save-btn > button {
        background-color: #00FF7F !important;
        color: black !important;
        height: 60px;
        font-weight: 800;
    }
    
    /* Score Card */
    .metric-card {
        background-color: #1c1f26;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00FF7F;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Página1", usecols=list(range(14)), ttl=0) # ttl=0 para não ter cache e ver água em tempo real
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=[
            'Data', 'Peso', 'Sono', 'Energia', 'Treino', 
            'PA_Sis', 'PA_Dia', 'HRV', 'Agua_L', 
            'Dieta', 'Shot', 'Colaterais', 'Obs', 'BioScore'
        ])

df_bio = load_data()

# --- LÓGICA DE JOGO (XP & LEVELLING) ---
total_logs = len(df_bio)
nivel = int(total_logs / 7) + 1 # Sobe de nível a cada 7 registros (1 semana)
prox_nivel = (nivel * 7) - total_logs
titulos = {1: "Novato", 2: "Iniciado", 3: "Biohacker", 4: "Otimizado", 5: "Elite", 10: "Cyborg"}
titulo_atual = titulos.get(nivel, "Lenda")

# --- HEADER GAMIFICADO ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title(f"🧬 BioFlow: Nível {nivel}")
    st.progress(min((total_logs % 7) / 7, 1.0))
    st.caption(f"🛡️ Rank: **{titulo_atual}** | Falta {prox_nivel} dias para subir de nível.")

# --- LÓGICA DE ÁGUA INTELIGENTE (SESSION STATE) ---
# Verifica se já tem registro hoje na planilha para puxar a contagem
hoje_str = date.today().strftime("%Y-%m-%d")
dados_hoje = df_bio[df_bio['Data'] == hoje_str]

if 'agua_counter' not in st.session_state:
    if not dados_hoje.empty:
        # Recupera o quanto já bebeu hoje (convertendo Litros de volta para Garrafas)
        litros_salvos = float(dados_hoje.iloc[0]['Agua_L'])
        st.session_state.agua_counter = int(litros_salvos / 0.887)
    else:
        st.session_state.agua_counter = 0

# --- FUNÇÕES DE ÁGUA ---
def add_water():
    st.session_state.agua_counter += 1
def remove_water():
    if st.session_state.agua_counter > 0:
        st.session_state.agua_counter -= 1

# --- EXPANDER PRINCIPAL ---
with st.expander(f"📝 REGISTRO DIÁRIO ({hoje_str})", expanded=True):
    
    # --- ÁREA DE ÁGUA (FORA DO FORMULÁRIO PARA INTERATIVIDADE) ---
    st.markdown("### 💧 Hidratação (Check-in)")
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    
    with col_w1:
        st.button("➖", on_click=remove_water, use_container_width=True)
    with col_w3:
        st.button("➕", on_click=add_water, use_container_width=True)
    with col_w2:
        qtd_garrafas = st.session_state.agua_counter
        total_litros = qtd_garrafas * 0.887
        meta = 4.0 # Meta de 4 Litros
        pct = min(total_litros / meta, 1.0)
        
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{qtd_garrafas} Garrafas</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #aaa;'>{total_litros:.2f}L / {meta}L</p>", unsafe_allow_html=True)
        st.progress(pct)
        
        # Feedback Visual
        if pct >= 1.0: st.success("🏆 META BATIDA!")
        elif pct >= 0.5: st.info("👍 Metade do caminho")

    st.divider()

    # --- FORMULÁRIO GERAL ---
    with st.form("game_form"):
        st.markdown("### 📊 Status da Máquina")
        
        c_bio1, c_bio2 = st.columns(2)
        # Recupera peso anterior se existir
        last_peso = float(df_bio['Peso'].iloc[-1]) if not df_bio.empty else 90.0
        peso = c_bio1.number_input("Peso (kg)", 80.0, 130.0, last_peso, step=0.1)
        sono = c_bio2.slider("Sono (Noite Passada)", 0, 10, 7)
        
        c_p1, c_p2 = st.columns(2)
        pa_sis = c_p1.number_input("PA Sistólica", 90, 200, 120)
        pa_dia = c_p2.number_input("PA Diastólica", 50, 120, 80)
        
        st.markdown("### ⚔️ Missões do Dia")
        treino = st.multiselect("Treino Feito", ["Musculação", "HYROX", "Cardio", "Jiu-Jitsu", "OFF"])
        dieta = st.select_slider("Qualidade da Dieta", ["Lixo (-20pts)", "Parcial (+10pts)", "Limpa 100% (+30pts)"])
        
        c_h1, c_h2 = st.columns(2)
        shot = c_h1.checkbox("💉 Shot Durateston")
        colaterais = c_h2.multiselect("Debuffs (Sintomas)", ["Acne", "Libido Baixa", "Irritabilidade", "Dores"])
        
        obs = st.text_area("Diário de Campanha (Obs):", height=80)
        
        # --- CÁLCULO DO BIOSCORE (Lógica Secreta) ---
        score_prev = 0
        score_prev += sono * 4 # Máx 40
        if "Limpa" in dieta: score_prev += 30
        elif "Parcial" in dieta: score_prev += 10
        else: score_prev -= 10
        if treino and "OFF" not in treino: score_prev += 20
        if total_litros >= 3.0: score_prev += 10 # Bonus Hidratação
        score_prev = max(0, min(100, score_prev)) # Limita entre 0 e 100
        
        st.caption(f"Score Estimado do Dia: {score_prev}/100")

        # Botão Salvar
        submit = st.form_submit_button("✅ SALVAR PROGRESSO")
        
        if submit:
            # LÓGICA DE DIÁRIO INTELIGENTE (ACUMULATIVO)
            obs_final = obs # Começa com o que você digitou agora
            
            # Se já tiver dados hoje, vamos tentar recuperar o diário antigo para não perder
            if not df_bio.empty and df_bio.iloc[-1]['Data'] == date.today().strftime("%Y-%m-%d"):
                obs_antiga = str(df_bio.iloc[-1]['Obs'])
                # Se a obs antiga não for vazia e não for igual a nova (pra não duplicar se clicar 2x)
                if obs_antiga != "nan" and obs_antiga != "" and obs not in obs_antiga:
                    time_now = datetime.now().strftime("%H:%M")
                    obs_final = f"{obs_antiga} | [{time_now}] {obs}"

            # Prepara dados (agora usando o obs_final acumulado)
            new_entry = pd.DataFrame([{
                'Data': date.today().strftime("%Y-%m-%d"),
                'Peso': peso,
                'Sono': sono,
                'Energia': "Calc", 
                'Treino': ", ".join(treino) if treino else "OFF",
                'PA_Sis': pa_sis,
                'PA_Dia': pa_dia,
                'HRV': "-",
                'Agua_L': total_litros, 
                'Dieta': dieta,
                'Shot': "SIM" if shot else "NÃO",
                'Colaterais': ", ".join(colaterais),
                'Obs': obs_final, # <--- AQUI ESTÁ A MÁGICA
                'BioScore': score_prev
            }])
            
            # (O resto do código de update continua igual...)
            try:
                df_final = df_bio.copy()
                if not df_final.empty and df_final.iloc[-1]['Data'] == date.today().strftime("%Y-%m-%d"):
                    df_final.iloc[-1] = new_entry.iloc[0] 
                    msg = "🔄 Diário de hoje ATUALIZADO (Notas adicionadas)!"
                else:
                    df_final = pd.concat([df_final, new_entry], ignore_index=True)
                    msg = "💾 Novo dia iniciado!"
                
                conn.update(worksheet="Página1", data=df_final)
                st.success(f"{msg}")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro: {e}")

# --- DASHBOARD DE EVOLUÇÃO ---
st.divider()
tab1, tab2 = st.tabs(["🏆 Performance", "🤖 Coach"])

with tab1:
    if 'BioScore' in df_bio.columns and not df_bio.empty:
        # Gráfico de Score
        st.markdown("##### Evolução do BioScore (Sua Nota)")
        chart = alt.Chart(df_bio.tail(14)).mark_area(
            line={'color':'#00FF7F'},
            color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#00FF7F', offset=0), alt.GradientStop(color='transparent', offset=1)], x1=1, x2=1, y1=1, y2=0)
        ).encode(
            x='Data',
            y=alt.Y('BioScore', scale=alt.Scale(domain=[0, 100])),
            tooltip=['Data', 'BioScore', 'Treino']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

with tab2:
    if st.button("Gerar Análise do Jogo"):
         recents = df_bio.tail(3).to_markdown() if not df_bio.empty else "Sem dados"
         prompt = f"""
         [BIOFLOW GAME DATA]
         User Level: {nivel} ({titulo_atual})
         
         RECENT LOGS:
         {recents}
         
         MISSÃO: Analise o BioScore. Onde o jogador está perdendo pontos? (Sono? Dieta?). Dê missões para subir o score amanhã.
         """
         st.code(prompt, language="text")
