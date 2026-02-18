"""
MAIN - Interface Streamlit do Agente Comprimoveis
Design Premium - inspirado no Calendario BPO Comprimoveis v2.0
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.services.ai_router import processar_mensagem
from app.services.gemini_service import listar_tarefas, listar_pendentes
from app.core.database import criar_tabelas, popular_condominios, SessionLocal

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================

st.set_page_config(
    page_title="Agente Comprimóveis",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS PREMIUM
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');

/* ========== VARIÁVEIS ========== */
:root {
    --azul-comprimoveis: #1a2942;
    --laranja-comprimoveis: #ff6b35;
    --azul-claro: #3d5a80;
    --verde-sucesso: #10b981;
    --vermelho-urgente: #ef4444;
}

/* ========== GLOBAL ========== */
* { font-family: 'Poppins', sans-serif !important; }

.stApp {
    background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 50%, #f0f4f8 100%) !important;
    min-height: 100vh;
}

/* ========== HEADER PREMIUM ========== */
.main-header {
    background: linear-gradient(135deg, rgba(26,41,66,0.97) 0%, rgba(61,90,128,0.97) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 2.2rem 2.5rem;
    border-radius: 24px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.1);
    animation: slideDown 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent 0%, #ff6b35 50%, transparent 100%);
    animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

.main-header::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,107,53,0.4), transparent);
}

@keyframes slideDown {
    from { opacity: 0; transform: translateY(-30px); }
    to   { opacity: 1; transform: translateY(0); }
}

.main-header h1 {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0.4rem 0 0.3rem 0;
    letter-spacing: -0.02em;
    position: relative;
    z-index: 2;
    text-shadow: 0 2px 20px rgba(0,0,0,0.3);
}

.main-header p {
    margin: 0.3rem 0 0 0;
    font-size: 1rem;
    opacity: 0.85;
    position: relative;
    z-index: 2;
    font-weight: 300;
    letter-spacing: 0.02em;
}

.header-logo-text {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    opacity: 0.6;
    position: relative;
    z-index: 2;
    margin-bottom: 0.5rem;
}

/* ========== STATS CARDS PREMIUM ========== */
.stat-card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 1.8rem 1.5rem;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.5);
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    animation: scaleIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    position: relative;
    overflow: hidden;
    cursor: default;
}

.stat-card::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--azul-comprimoveis), var(--laranja-comprimoveis));
    transform: scaleX(0);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.stat-card:hover::before { transform: scaleX(1); }

.stat-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 50px rgba(255, 107, 53, 0.2);
}

@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.85); }
    to   { opacity: 1; transform: scale(1); }
}

.stat-icon {
    font-size: 1.8rem;
    margin-bottom: 0.3rem;
    display: block;
}

.stat-number {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--azul-comprimoveis) 0%, var(--laranja-comprimoveis) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.2rem 0;
    font-family: 'Space Mono', monospace !important;
    line-height: 1;
    display: block;
}

.stat-label {
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.4rem;
    display: block;
}

/* ========== CHAT SECTION ========== */
.chat-section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--azul-comprimoveis);
    margin-bottom: 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid rgba(255,107,53,0.2);
    letter-spacing: -0.01em;
}

.chat-container {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 1.5rem;
    min-height: 340px;
    max-height: 420px;
    overflow-y: auto;
    border: 1px solid rgba(255,255,255,0.6);
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
    scroll-behavior: smooth;
}

.chat-container::-webkit-scrollbar { width: 5px; }
.chat-container::-webkit-scrollbar-track { background: transparent; }
.chat-container::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #1a2942, #3d5a80);
    border-radius: 10px;
}

.chat-msg-user {
    background: linear-gradient(135deg, var(--azul-comprimoveis) 0%, var(--azul-claro) 100%);
    color: white;
    padding: 0.85rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.6rem 0 0.6rem 18%;
    box-shadow: 0 4px 15px rgba(26,41,66,0.25);
    font-size: 0.92rem;
    line-height: 1.5;
    animation: msgIn 0.3s ease;
}

.chat-msg-agente {
    background: white;
    color: #1a2942;
    padding: 0.85rem 1.2rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.6rem 18% 0.6rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    border: 1px solid rgba(61,90,128,0.1);
    font-size: 0.92rem;
    line-height: 1.5;
    animation: msgIn 0.3s ease;
}

.chat-msg-agente::before {
    content: '🤖 ';
    font-size: 0.8rem;
    opacity: 0.6;
}

@keyframes msgIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ========== INPUT E BOTÃO ========== */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 2px solid rgba(61,90,128,0.2) !important;
    padding: 0.7rem 1rem !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    background: rgba(255,255,255,0.9) !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--laranja-comprimoveis) !important;
    box-shadow: 0 0 0 3px rgba(255,107,53,0.15) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--laranja-comprimoveis) 0%, #ff8c61 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 6px 20px rgba(255,107,53,0.35) !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 10px 30px rgba(255,107,53,0.45) !important;
}

.stButton > button:active {
    transform: translateY(-1px) scale(0.99) !important;
}

/* ========== TASK CARDS PREMIUM ========== */
.tarefas-section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--azul-comprimoveis);
    margin-bottom: 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid rgba(255,107,53,0.2);
    letter-spacing: -0.01em;
}

.tarefa-card {
    background: white;
    border-left: 5px solid var(--laranja-comprimoveis);
    padding: 1.1rem 1.3rem;
    margin: 0.7rem 0;
    border-radius: 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    color: #1a2942 !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.tarefa-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 5px;
    background: linear-gradient(180deg, var(--laranja-comprimoveis), #ff8c61);
    border-radius: 0 0 0 16px;
}

.tarefa-card:hover {
    transform: translateX(4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.tarefa-card strong {
    color: #1a2942 !important;
    font-weight: 600;
    font-size: 0.92rem;
}

.tarefa-card small {
    color: #64748b !important;
    font-size: 0.8rem;
}

.tarefa-card .tarefa-badge {
    display: inline-block;
    background: rgba(61,90,128,0.1);
    color: #3d5a80;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.4rem;
}

.tarefa-concluida {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border-left-color: var(--verde-sucesso) !important;
    opacity: 0.92;
    color: #065f46 !important;
}

.tarefa-concluida::before {
    background: linear-gradient(180deg, #10b981, #34d399) !important;
}

.tarefa-concluida strong { color: #065f46 !important; }
.tarefa-concluida small  { color: #6ee7b7 !important; }

.tarefa-urgente {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border-left-color: var(--vermelho-urgente) !important;
    color: #991b1b !important;
    animation: urgentPulse 2.5s ease-in-out infinite;
}

.tarefa-urgente::before {
    background: linear-gradient(180deg, #ef4444, #f87171) !important;
}

@keyframes urgentPulse {
    0%, 100% { box-shadow: 0 4px 15px rgba(0,0,0,0.06); }
    50%       { box-shadow: 0 4px 15px rgba(239,68,68,0.25), 0 0 0 3px rgba(239,68,68,0.08); }
}

/* ========== SECTION BOX ========== */
.section-box {
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 1.5rem;
    border: 1px solid rgba(255,255,255,0.6);
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
}

/* ========== EMPTY STATE ========== */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #94a3b8;
}

.empty-state .empty-icon { font-size: 2.5rem; margin-bottom: 0.8rem; display: block; }
.empty-state p { font-size: 0.9rem; margin: 0; }

/* ========== INFO BOX ========== */
.stInfo {
    border-radius: 12px !important;
    background: rgba(61,90,128,0.08) !important;
    border: 1px solid rgba(61,90,128,0.2) !important;
}

/* ========== RODAPÉ ========== */
.footer-premium {
    text-align: center;
    padding: 1.5rem 0 0.5rem 0;
    color: #94a3b8;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
}

.footer-premium strong { color: #64748b; }

/* ========== SPINNER ========== */
.stSpinner > div { border-color: var(--laranja-comprimoveis) transparent transparent transparent !important; }

/* ========== FORM ========== */
.stForm {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* ========== RESPONSIVO ========== */
@media (max-width: 768px) {
    .main-header h1 { font-size: 1.6rem; }
    .stat-number    { font-size: 2.2rem; }
    .chat-msg-user  { margin-left: 8%; }
    .chat-msg-agente { margin-right: 8%; }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# INICIALIZACAO
# ============================================================

@st.cache_resource
def inicializar_banco():
    criar_tabelas()
    popular_condominios()
    return True

inicializar_banco()


# ============================================================
# HEADER PREMIUM
# ============================================================

st.markdown("""
<div class="main-header">
    <div class="header-logo-text">Comprimóveis — Consultoria &amp; Administração</div>
    <h1>🏢 Agente Comprimóveis</h1>
    <p>Assistente inteligente para gestão de condomínios · Powered by Gemini AI</p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# STATS
# ============================================================

db = SessionLocal()
hoje = datetime.now()
tarefas_pendentes = listar_pendentes(db, mes=hoje.month, ano=hoje.year)
tarefas_todas = listar_tarefas(db, mes=hoje.month, ano=hoje.year)
db.close()

total_pendentes = len(tarefas_pendentes)
total_concluidas = len([t for t in tarefas_todas if t['status'] == 'concluida'])
total_urgentes = len([t for t in tarefas_pendentes if t['urgente']])

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-icon">📋</span>
        <span class="stat-number">{total_pendentes}</span>
        <span class="stat-label">Pendentes</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-icon">✅</span>
        <span class="stat-number">{total_concluidas}</span>
        <span class="stat-label">Concluídas</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <span class="stat-icon">🚨</span>
        <span class="stat-number">{total_urgentes}</span>
        <span class="stat-label">Urgentes</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

col_chat, col_tarefas = st.columns([1.2, 1])


# ── COLUNA CHAT ──
with col_chat:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="chat-section-title">💬 Fale com o Agente</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.85rem;color:#64748b;margin:-0.5rem 0 1rem 0;"
        "font-style:italic;'>Digite naturalmente — crie tarefas, marque como pago, pergunte pendências...</p>",
        unsafe_allow_html=True
    )

    # Inicializa histórico
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = [
            {
                "role": "agente",
                "texto": "Olá, Vanessa! 👋 Sou seu assistente da Comprimóveis. Como posso ajudar hoje?"
            }
        ]

    # Renderiza histórico num container scrollável
    msgs_html = ""
    for msg in st.session_state.historico_chat:
        if msg["role"] == "user":
            msgs_html += f'<div class="chat-msg-user">{msg["texto"]}</div>'
        else:
            msgs_html += f'<div class="chat-msg-agente">{msg["texto"]}</div>'

    st.markdown(f'<div class="chat-container">{msgs_html}</div>', unsafe_allow_html=True)

    # Input do usuário
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Mensagem",
            placeholder="Ex: Adiciona boleto da Light dia 15 Village Mananciais",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("📨 Enviar", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if submitted and user_input:
        st.session_state.historico_chat.append({
            "role": "user",
            "texto": user_input
        })

        with st.spinner("Processando..."):
            resultado = asyncio.run(processar_mensagem(user_input))

        st.session_state.historico_chat.append({
            "role": "agente",
            "texto": resultado["resposta"]
        })

        st.rerun()


# ── COLUNA TAREFAS ──
with col_tarefas:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="tarefas-section-title">📋 Tarefas do Mês</div>', unsafe_allow_html=True)

    if not tarefas_todas:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-icon">📭</span>
            <p>Nenhuma tarefa este mês.<br>Use o chat para adicionar!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Pendentes
        pendentes = [t for t in tarefas_todas if t['status'] == 'pendente']
        if pendentes:
            st.markdown(
                "<p style='font-size:0.8rem;font-weight:700;color:#64748b;"
                "text-transform:uppercase;letter-spacing:0.08em;margin:0.5rem 0;'>Pendentes</p>",
                unsafe_allow_html=True
            )
            for t in pendentes:
                classe = "tarefa-urgente" if t['urgente'] else "tarefa-card"
                dia = f"📅 Dia {t['dia']}  " if t['dia'] else ""
                urgente_tag = " 🚨 <em>URGENTE</em>" if t['urgente'] else ""
                st.markdown(f"""
                <div class="{classe}">
                    <strong>[{t['id']}] {t['titulo']}{urgente_tag}</strong><br>
                    <small>{dia}🏢 {t['condominio']} · {t['categoria']}</small>
                </div>
                """, unsafe_allow_html=True)

        # Concluídas
        concluidas = [t for t in tarefas_todas if t['status'] == 'concluida']
        if concluidas:
            st.markdown(
                "<p style='font-size:0.8rem;font-weight:700;color:#64748b;"
                "text-transform:uppercase;letter-spacing:0.08em;margin:1rem 0 0.5rem 0;'>Concluídas</p>",
                unsafe_allow_html=True
            )
            for t in concluidas:
                dia = f"📅 Dia {t['dia']}  " if t['dia'] else ""
                st.markdown(f"""
                <div class="tarefa-concluida tarefa-card">
                    <strong>✅ {t['titulo']}</strong><br>
                    <small>{dia}🏢 {t['condominio']}</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# RODAPÉ
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div class="footer-premium">
    <strong>Comprimóveis</strong> · Consultoria &amp; Administração de Condomínios<br>
    Agente v1.0 · Powered by Gemini AI · {hoje.strftime('%B %Y')}
</div>
""", unsafe_allow_html=True)
