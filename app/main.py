"""
MAIN - Interface Streamlit do Agente Comprimoveis
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
    page_title="Agente Comprimoveis",
    page_icon="🏢",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');

* { font-family: 'Poppins', sans-serif; }

.main { background: linear-gradient(135deg, #f8fafc, #e2e8f0); }

.header {
    background: linear-gradient(135deg, #1a2942, #3d5a80);
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    text-align: center;
}

.header h1 {
    color: white;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
}

.header p {
    color: rgba(255,255,255,0.7);
    margin: 0.5rem 0 0 0;
}

.stat-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-top: 4px solid #ff6b35;
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 800;
    color: #ff6b35;
}

.stat-label {
    color: #64748b;
    font-size: 0.9rem;
    font-weight: 600;
}

.tarefa-card {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-left: 4px solid #3d5a80;
}

.tarefa-card.urgente {
    border-left-color: #ef4444;
}

.tarefa-card.concluida {
    border-left-color: #10b981;
    opacity: 0.7;
}

.chat-msg-user {
    background: #1a2942;
    color: white;
    padding: 0.8rem 1.2rem;
    border-radius: 16px 16px 4px 16px;
    margin: 0.5rem 0;
    margin-left: 20%;
    text-align: right;
}

.chat-msg-agente {
    background: white;
    color: #1a2942;
    padding: 0.8rem 1.2rem;
    border-radius: 16px 16px 16px 4px;
    margin: 0.5rem 0;
    margin-right: 20%;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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
# HEADER
# ============================================================

st.markdown("""
<div class="header">
    <h1>🏢 Agente Comprimoveis</h1>
    <p>Assistente inteligente para gestao de condominios</p>
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
        <div class="stat-number">{total_pendentes}</div>
        <div class="stat-label">Pendentes</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_concluidas}</div>
        <div class="stat-label">Concluidas</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_urgentes}</div>
        <div class="stat-label">Urgentes</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

col_chat, col_tarefas = st.columns([1.2, 1])


# ── COLUNA CHAT ──
with col_chat:
    st.markdown("### 💬 Fale com o Agente")
    st.markdown("*Digite naturalmente — adicione tarefas, marque como pago, pergunte pendências...*")

    # Inicializa histórico
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = [
            {
                "role": "agente",
                "texto": "Ola Vanessa! Sou seu assistente da Comprimoveis. Como posso ajudar hoje?"
            }
        ]

    # Mostra histórico
    for msg in st.session_state.historico_chat:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">{msg["texto"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-agente">{msg["texto"]}</div>', unsafe_allow_html=True)

    # Input do usuário
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Mensagem",
            placeholder="Ex: Adiciona boleto da Light dia 15 Village Mananciais",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("Enviar", use_container_width=True)

    if submitted and user_input:
        # Adiciona mensagem do usuário
        st.session_state.historico_chat.append({
            "role": "user",
            "texto": user_input
        })

        # Processa com o agente
        with st.spinner("Processando..."):
            resultado = asyncio.run(processar_mensagem(user_input))

        # Adiciona resposta do agente
        st.session_state.historico_chat.append({
            "role": "agente",
            "texto": resultado["resposta"]
        })

        st.rerun()


# ── COLUNA TAREFAS ──
with col_tarefas:
    st.markdown("### 📋 Tarefas do Mes")

    if not tarefas_todas:
        st.info("Nenhuma tarefa este mes. Use o chat para adicionar!")
    else:
        # Pendentes
        pendentes = [t for t in tarefas_todas if t['status'] == 'pendente']
        if pendentes:
            st.markdown("**Pendentes:**")
            for t in pendentes:
                urgente_class = "urgente" if t['urgente'] else ""
                dia = f"Dia {t['dia']} - " if t['dia'] else ""
                st.markdown(f"""
                <div class="tarefa-card {urgente_class}">
                    <strong>[{t['id']}] {dia}{t['titulo']}</strong><br>
                    <small>{t['condominio']} • {t['categoria']}</small>
                </div>
                """, unsafe_allow_html=True)

        # Concluidas
        concluidas = [t for t in tarefas_todas if t['status'] == 'concluida']
        if concluidas:
            st.markdown("**Concluidas:**")
            for t in concluidas:
                dia = f"Dia {t['dia']} - " if t['dia'] else ""
                st.markdown(f"""
                <div class="tarefa-card concluida">
                    <strong>✅ {dia}{t['titulo']}</strong><br>
                    <small>{t['condominio']}</small>
                </div>
                """, unsafe_allow_html=True)


# ============================================================
# RODAPE
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<center><small>Agente Comprimoveis v1.0 • Powered by Gemini AI</small></center>",
    unsafe_allow_html=True
)