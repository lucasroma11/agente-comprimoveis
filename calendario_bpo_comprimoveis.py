"""
🏢 SISTEMA DE CALENDÁRIO BPO - COMPRIMÓVEIS
Consultoria & Administração - "A chave do seu sonho está aqui"

Sistema de Gerenciamento de Tarefas Mensais
Para: Vanessa (Administração)
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd
import json

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Calendário BPO - Comprimóveis",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS CUSTOMIZADO - IDENTIDADE COMPRIMÓVEIS
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');
    
    :root {
        --primary: #1a2942;
        --accent: #ff6b35;
        --accent-light: #ff8c61;
        --success: #10b981;
        --glass-bg: rgba(255, 255, 255, 0.7);
        --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.12);
        --shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.18);
        --shadow-glow: 0 0 40px rgba(255, 107, 53, 0.3);
    }
    
    * { font-family: 'Poppins', sans-serif; }
    
    /* Background Animado */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Header Premium */
    .main-header {
        background: linear-gradient(135deg, rgba(26, 41, 66, 0.95), rgba(45, 66, 99, 0.95));
        backdrop-filter: blur(20px);
        padding: 3rem 2rem;
        border-radius: 24px;
        margin-bottom: 3rem;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: slideDown 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header img {
        max-width: 280px;
        margin-bottom: 1.5rem;
        filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.3));
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.15rem;
        margin: 0.75rem 0;
    }
    
    /* Stats Cards Premium */
    .stat-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: var(--shadow-md);
        transition: all 0.4s ease;
        animation: scaleIn 0.5s ease both;
    }
    
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    
    .stat-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }
    
    .stat-number {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Space Mono', monospace;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        color: #64748b;
        font-size: 0.95rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Task Cards Premium */
    .tarefa-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid var(--accent);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        color: #1e293b !important;
    }
    
    .tarefa-card:hover {
        transform: translateX(4px);
        box-shadow: var(--shadow-md);
    }
    
    .tarefa-card strong { color: #1a2942 !important; }
    .tarefa-card small { color: #666 !important; }
    
    .tarefa-concluida {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        border-left-color: var(--success);
        opacity: 0.85;
    }
    
    .tarefa-urgente {
        background: linear-gradient(135deg, #fef2f2, #fee2e2);
        border-left-color: #ef4444;
        animation: urgentPulse 2s ease-in-out infinite;
    }
    
    @keyframes urgentPulse {
        0%, 100% { box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
        50% { box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1); }
    }
    
    .cond-badge {
        background: linear-gradient(135deg, var(--primary), #2d4263);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(26, 41, 66, 0.2);
        display: inline-block;
    }
    
    /* Buttons Premium */
    .stButton>button {
        background: linear-gradient(135deg, var(--accent), var(--accent-light));
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 24px rgba(255, 107, 53, 0.4);
    }
    
    /* Progress Bar Premium */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent), var(--accent-light));
        border-radius: 10px;
        height: 12px;
    }
    
    /* Tabs Premium */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary), #2d4263);
        color: white !important;
        box-shadow: 0 4px 12px rgba(26, 41, 66, 0.3);
        border-radius: 8px;
    }
    
    /* Scrollbar Premium */
    ::-webkit-scrollbar { width: 12px; }
    ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.05); border-radius: 10px; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--primary), var(--accent));
        border-radius: 10px;
        border: 2px solid rgba(255, 255, 255, 0.5);
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 2rem; }
        .stat-number { font-size: 2.5rem; }
    }
</style>

""", unsafe_allow_html=True)

# ============================================================================
# DADOS DO CALENDÁRIO BPO
# ============================================================================

# Estrutura de tarefas por dia
TAREFAS_POR_DIA = {
    1: [
        {
            "condominio": "Village Mananciais", 
            "tipo": "Transferência", 
            "descricao": "Transfer CX Presidente Fátima - Recarga Interfones",
            "destinatario": "Fátima (Presidente)",
            "valor": 100.00
        },
        {
            "condominio": "Colina Verde", 
            "tipo": "Boleto", 
            "descricao": "Iguá - Débito em conta automático",
            "destinatario": "Conta Santander Ag. 3894",
            "valor": None
        }
    ],
    5: [
        {"condominio": "Village Tucanos", "tipo": "Pagamento", "descricao": "Salários dos Funcionários (Bruno e Gustavo)", "valor": 3850.00},
        {"condominio": "Itaipu", "tipo": "Boleto", "descricao": "Bem mais gestora", "valor": None},
        {"condominio": "Itaipu", "tipo": "PIX", "descricao": "Salários Funcionários (Antônio e José)", "valor": None},
        {"condominio": "Samira", "tipo": "PIX", "descricao": "Allan Diego (Síndico Profissional)", "valor": None},
        {"condominio": "Colina Verde", "tipo": "Boleto", "descricao": "Bem mais gestora", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "Boleto", "descricao": "WN Tecnologia + Bem mais + Iguá", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "PIX", "descricao": "Salários 6 Funcionários", "valor": None}
    ],
    8: [
        {"condominio": "Anchieta", "tipo": "Boleto", "descricao": "Iguá - Matrícula 537256-9", "valor": None},
        {"condominio": "Village Ipadu", "tipo": "Transferência", "descricao": "CX Presidente Washington", "valor": None}
    ],
    10: [
        {"condominio": "Anchieta", "tipo": "Boleto", "descricao": "Light - Matrícula 011606195", "valor": None},
        {"condominio": "Anchieta", "tipo": "Pagamento", "descricao": "Prestador Interfone (Marcos Vieira)", "valor": None},
        {"condominio": "Anchieta", "tipo": "Boleto", "descricao": "Taquara Net", "valor": None},
        {"condominio": "Sylvania", "tipo": "PIX", "descricao": "Funcionários/Prestadores (Jorge e Mário)", "valor": 1450.00},
        {"condominio": "Village Pedras", "tipo": "PIX", "descricao": "Gota D'Água Piscinas + Suelena", "valor": 5360.00},
        {"condominio": "Samira", "tipo": "Boleto", "descricao": "Light", "valor": None},
        {"condominio": "Samira", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 985,98)", "valor": 985.98},
        {"condominio": "Village Tucanos", "tipo": "PIX", "descricao": "Prestadores (Magno, Elias, José)", "valor": 2200.00},
        {"condominio": "Colina Verde", "tipo": "Boleto", "descricao": "Alpha Manutenção", "valor": None}
    ],
    15: [
        {"condominio": "Anchieta", "tipo": "PIX", "descricao": "Letícia (Faxineira) R$ 550", "valor": 550.00},
        {"condominio": "Anchieta", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 563)", "valor": 563.00},
        {"condominio": "Primavera", "tipo": "PIX", "descricao": "Cláudio de Oliveira R$ 150", "valor": 150.00},
        {"condominio": "Primavera", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 642,80)", "valor": 642.80},
        {"condominio": "Sylvania", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 582,50)", "valor": 582.50},
        {"condominio": "Sylvania", "tipo": "Boleto", "descricao": "Águas do Rio", "valor": None},
        {"condominio": "Village Ipadu", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 1.111,46)", "valor": 1111.46},
        {"condominio": "Village Ipadu", "tipo": "Boleto", "descricao": "Olá Fibra Internet", "valor": None},
        {"condominio": "Village Mananciais", "tipo": "Boleto", "descricao": "SISGU Segurança", "valor": 488.00},
        {"condominio": "Village Mananciais", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 859,38)", "valor": 859.38},
        {"condominio": "Village Pedras", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 1.250)", "valor": 1250.00},
        {"condominio": "Village Pedras", "tipo": "PIX", "descricao": "Adiantamento Salários (8 funcionários)", "valor": None},
        {"condominio": "Itaipu", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 1.746,33)", "valor": 1746.33},
        {"condominio": "Samira", "tipo": "Boleto", "descricao": "Naturgy", "valor": None},
        {"condominio": "Village Tucanos", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 902,42)", "valor": 902.42},
        {"condominio": "Village Tucanos", "tipo": "PIX", "descricao": "Suzana (Ajuda custo) R$ 350", "valor": 350.00},
        {"condominio": "Colina Verde", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 977)", "valor": 977.00},
        {"condominio": "Colina Verde", "tipo": "Boleto", "descricao": "Claro + Naturgy", "valor": None},
        {"condominio": "Colina Verde", "tipo": "PIX", "descricao": "Adiantamento Salários (2 funcionários)", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "Transferência", "descricao": "TX ADM Comprimóveis (R$ 977)", "valor": 977.00},
        {"condominio": "Nascente Rio Grande", "tipo": "Boleto", "descricao": "Semear Internet + Claro", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "PIX", "descricao": "Adiantamento Salários (6 funcionários)", "valor": None}
    ],
    19: [
        {"condominio": "Village Pedras", "tipo": "Impostos", "descricao": "FGTS + INSS", "valor": None},
        {"condominio": "Village Pedras", "tipo": "Boleto", "descricao": "Iguá + Claro", "valor": None},
        {"condominio": "Samira", "tipo": "Impostos", "descricao": "FGTS + INSS", "valor": None},
        {"condominio": "Samira", "tipo": "Boleto", "descricao": "Iguá + Claro", "valor": None},
        {"condominio": "Colina Verde", "tipo": "Impostos", "descricao": "FGTS + INSS", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "Impostos", "descricao": "FGTS + INSS", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "Boleto", "descricao": "Jurídico R$ 1.860,56", "valor": 1860.56}
    ],
    20: [
        {"condominio": "Primavera", "tipo": "Boleto", "descricao": "Iguá + Light", "valor": None},
        {"condominio": "Sylvania", "tipo": "Boleto", "descricao": "Light - Matrícula 0411681294", "valor": None},
        {"condominio": "Village Mananciais", "tipo": "Boleto", "descricao": "NIO Fibra", "valor": None},
        {"condominio": "Village Pedras", "tipo": "Boleto", "descricao": "Hidroluz + Light (3 endereços)", "valor": None},
        {"condominio": "Itaipu", "tipo": "Boleto", "descricao": "Seguro Predial R$ 727,90", "valor": 727.90}
    ],
    25: [
        {"condominio": "Primavera", "tipo": "Transferência", "descricao": "CX Síndico Agapito", "valor": None},
        {"condominio": "Village Mananciais", "tipo": "Boleto", "descricao": "Light - Matrícula 430139742", "valor": None},
        {"condominio": "Samira", "tipo": "Boleto", "descricao": "Elevadores Atlas", "valor": None}
    ],
    26: [
        {"condominio": "Colina Verde", "tipo": "Boleto", "descricao": "Light - Débito em conta", "valor": None},
        {"condominio": "Nascente Rio Grande", "tipo": "Boleto", "descricao": "Light - Débito + Sulamérica", "valor": None}
    ],
    28: [
        {"condominio": "Village Pedras", "tipo": "Vale", "descricao": "VR Refeição + Vale Transporte", "valor": None},
        {"condominio": "Village Pedras", "tipo": "Pagamento", "descricao": "Salários 8 Funcionários", "valor": None}
    ],
    30: [
        {"condominio": "Colina Verde", "tipo": "PIX", "descricao": "Salários Funcionários (Almir e Severino)", "valor": None},
        {"condominio": "Colina Verde", "tipo": "Boleto", "descricao": "Triangular Elevadores", "valor": None}
    ]
}

# Lista de todos os condomínios
CONDOMINIOS = [
    "Village Mananciais", "Colina Verde", "Village Tucanos", "Itaipu",
    "Samira", "Nascente Rio Grande", "Anchieta", "Village Ipadu",
    "Sylvania", "Village Pedras", "Primavera"
]

# ============================================================================
# HEADER PRINCIPAL COM LOGO
# ============================================================================

# Carrega a logo do GitHub
logo_url = "https://raw.githubusercontent.com/lucasroma11/agente-comprimoveis/main/logo-comprimoveis-1.png"

st.markdown(f"""
<div class="main-header">
    <img src="{logo_url}" alt="Comprimóveis" style="max-width: 200px; margin-bottom: 1rem;">
    <h1>🏢 Calendário BPO - Comprimóveis</h1>
    <p>Consultoria & Administração</p>
    <p style="font-size: 1rem; margin-top: 0.5rem;">"A chave do seu sonho está aqui"</p>
    <p style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.8;">CRECI: 37215 | Sistema de Gerenciamento para Vanessa</p>
</div>
""", unsafe_allow_html=True)
# ============================================================================
# INICIALIZAÇÃO DO ESTADO
# ============================================================================

if 'tarefas_concluidas' not in st.session_state:
    st.session_state.tarefas_concluidas = {}

if 'mes_atual' not in st.session_state:
    st.session_state.mes_atual = datetime.now().month

if 'ano_atual' not in st.session_state:
    st.session_state.ano_atual = datetime.now().year

# ============================================================================
# SIDEBAR - FILTROS E CONFIGURAÇÕES
# ============================================================================

with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    st.markdown("---")
    
    # Seleção de data
    col1, col2 = st.columns(2)
    with col1:
        mes_selecionado = st.selectbox(
            "Mês",
            range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda x: [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ][x-1]
        )
    
    with col2:
        ano_selecionado = st.selectbox(
            "Ano",
            [2025, 2026, 2027],
            index=1 if datetime.now().year == 2026 else 0
        )
    
    st.session_state.mes_atual = mes_selecionado
    st.session_state.ano_atual = ano_selecionado
    
    st.markdown("---")
    
    # Filtro por condomínio
    st.markdown("### 🏢 Filtrar por Condomínio")
    condominio_filtro = st.multiselect(
        "Selecione:",
        ["Todos"] + CONDOMINIOS,
        default=["Todos"]
    )
    
    st.markdown("---")
    
    # Filtro por tipo
    st.markdown("### 📋 Filtrar por Tipo")
    tipo_filtro = st.multiselect(
        "Selecione:",
        ["Todos", "Boleto", "PIX", "Transferência", "Pagamento", "Impostos", "Vale"],
        default=["Todos"]
    )
    
    st.markdown("---")
    
    # Botões de ação
    if st.button("🔄 Resetar Tarefas do Mês"):
        chave_mes = f"{st.session_state.mes_atual}/{st.session_state.ano_atual}"
        if chave_mes in st.session_state.tarefas_concluidas:
            del st.session_state.tarefas_concluidas[chave_mes]
        st.success("✅ Tarefas resetadas!")
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📞 Contatos")
    st.markdown("""
    **Telefones:**  
    (21) 3933-4137  
    (21) 2421-3375
    
    **WhatsApp:**  
    (21) 99372-1324
    
    **Endereço:**  
    Estrada dos Três Rios, 1200  
    Sala 620, Freguesia - RJ
    """)

# ============================================================================
# ESTATÍSTICAS PRINCIPAIS
# ============================================================================

# Calcula estatísticas
total_tarefas = sum(len(tarefas) for tarefas in TAREFAS_POR_DIA.values())
chave_mes = f"{st.session_state.mes_atual}/{st.session_state.ano_atual}"
tarefas_concluidas_mes = st.session_state.tarefas_concluidas.get(chave_mes, [])
total_concluidas = len(tarefas_concluidas_mes)
total_pendentes = total_tarefas - total_concluidas
progresso = (total_concluidas / total_tarefas * 100) if total_tarefas > 0 else 0

# Valor total estimado
valor_total = sum(
    tarefa.get("valor", 0) or 0
    for tarefas in TAREFAS_POR_DIA.values()
    for tarefa in tarefas
)

# Exibe estatísticas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_tarefas}</div>
        <div class="stat-label">Total de Tarefas</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_concluidas}</div>
        <div class="stat-label">✅ Concluídas</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_pendentes}</div>
        <div class="stat-label">⏳ Pendentes</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{progresso:.0f}%</div>
        <div class="stat-label">Progresso</div>
    </div>
    """, unsafe_allow_html=True)

# Barra de progresso
st.progress(progresso / 100)

st.markdown("---")

# ============================================================================
# TAREFAS DE HOJE (DESTAQUE)
# ============================================================================

dia_hoje = datetime.now().day
mes_hoje = datetime.now().month
ano_hoje = datetime.now().year

if (mes_hoje == st.session_state.mes_atual and 
    ano_hoje == st.session_state.ano_atual and 
    dia_hoje in TAREFAS_POR_DIA):
    
    st.markdown("### 🔔 Tarefas de HOJE")
    
    tarefas_hoje = TAREFAS_POR_DIA[dia_hoje]
    
    for idx, tarefa in enumerate(tarefas_hoje):
        chave_tarefa = f"{chave_mes}-{dia_hoje}-{idx}"
        concluida = chave_tarefa in tarefas_concluidas_mes
        
        col1, col2 = st.columns([0.9, 0.1])
        
        with col1:
            classe = "tarefa-concluida" if concluida else "tarefa-urgente"
            
            # Ícone por tipo
            icones = {
                "Boleto": "📄",
                "PIX": "💸",
                "Transferência": "💰",
                "Pagamento": "💵",
                "Impostos": "🏛️",
                "Vale": "🎫"
            }
            icone = icones.get(tarefa['tipo'], "📋")
            
            valor_str = f"<br><small style='color: #2e7d32; font-weight: bold;'>💰 R$ {tarefa['valor']:,.2f}</small>".replace(",", "X").replace(".", ",").replace("X", ".") if tarefa.get('valor') else ""
            
            destinatario_str = f"<br><small style='color: #666;'>👤 {tarefa.get('destinatario', '')}</small>" if tarefa.get('destinatario') else ""
            
            st.markdown(f"""
            <div class="tarefa-card {classe}">
                <span class="cond-badge">{tarefa['condominio']}</span><br>
                <strong style='color: #1a2942;'>{icone} {tarefa['tipo']}:</strong> 
                <span style='color: #333;'>{tarefa['descricao']}</span>
                {destinatario_str}
                {valor_str}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.checkbox("✓", value=concluida, key=f"hoje_{chave_tarefa}"):
                if chave_tarefa not in tarefas_concluidas_mes:
                    tarefas_concluidas_mes.append(chave_tarefa)
                    st.session_state.tarefas_concluidas[chave_mes] = tarefas_concluidas_mes
            else:
                if chave_tarefa in tarefas_concluidas_mes:
                    tarefas_concluidas_mes.remove(chave_tarefa)
                    st.session_state.tarefas_concluidas[chave_mes] = tarefas_concluidas_mes
    
    st.markdown("---")

# ============================================================================
# TODAS AS TAREFAS DO MÊS
# ============================================================================

st.markdown("### 📅 Todas as Tarefas do Mês")

# Abas por semana
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Dias 1-7", "📅 Dias 8-15", "📅 Dias 16-22", "📅 Dias 23-31", "📊 Resumo"
])

def exibir_tarefas_periodo(dias, tab):
    with tab:
        for dia in sorted(dias):
            if dia in TAREFAS_POR_DIA:
                st.markdown(f"#### 📆 Dia {dia}")
                
                tarefas = TAREFAS_POR_DIA[dia]
                
                # Aplicar filtros
                tarefas_filtradas = tarefas
                
                if "Todos" not in condominio_filtro:
                    tarefas_filtradas = [t for t in tarefas_filtradas if t['condominio'] in condominio_filtro]
                
                if "Todos" not in tipo_filtro:
                    tarefas_filtradas = [t for t in tarefas_filtradas if t['tipo'] in tipo_filtro]
                
                if not tarefas_filtradas:
                    st.info("Nenhuma tarefa para este dia com os filtros aplicados.")
                    continue
                
                for idx, tarefa in enumerate(tarefas_filtradas):
                    chave_tarefa = f"{chave_mes}-{dia}-{idx}"
                    concluida = chave_tarefa in tarefas_concluidas_mes
                    
                    col1, col2 = st.columns([0.9, 0.1])
                    
                    with col1:
                        classe = "tarefa-concluida" if concluida else "tarefa-card"
                        
                        # Ícone por tipo
                        icones = {
                            "Boleto": "📄",
                            "PIX": "💸",
                            "Transferência": "💰",
                            "Pagamento": "💵",
                            "Impostos": "🏛️",
                            "Vale": "🎫"
                        }
                        icone = icones.get(tarefa['tipo'], "📋")
                        
                        valor_str = f"<br><small style='color: #2e7d32; font-weight: bold;'>💰 R$ {tarefa['valor']:,.2f}</small>".replace(",", "X").replace(".", ",").replace("X", ".") if tarefa.get('valor') else ""
                        
                        destinatario_str = f"<br><small style='color: #666;'>👤 {tarefa.get('destinatario', '')}</small>" if tarefa.get('destinatario') else ""
                        
                        st.markdown(f"""
                        <div class="tarefa-card {classe}">
                            <span class="cond-badge">{tarefa['condominio']}</span><br>
                            <strong style='color: #1a2942;'>{icone} {tarefa['tipo']}:</strong> 
                            <span style='color: #333;'>{tarefa['descricao']}</span>
                            {destinatario_str}
                            {valor_str}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.checkbox("✓", value=concluida, key=f"dia{dia}_{idx}"):
                            if chave_tarefa not in tarefas_concluidas_mes:
                                tarefas_concluidas_mes.append(chave_tarefa)
                                st.session_state.tarefas_concluidas[chave_mes] = tarefas_concluidas_mes
                        else:
                            if chave_tarefa in tarefas_concluidas_mes:
                                tarefas_concluidas_mes.remove(chave_tarefa)
                                st.session_state.tarefas_concluidas[chave_mes] = tarefas_concluidas_mes
                
                st.markdown("---")

# Exibir tarefas por período
exibir_tarefas_periodo(range(1, 8), tab1)
exibir_tarefas_periodo(range(8, 16), tab2)
exibir_tarefas_periodo(range(16, 23), tab3)
exibir_tarefas_periodo(range(23, 32), tab4)

# Resumo
with tab5:
    st.markdown("### 📊 Resumo por Condomínio")
    
    resumo_cond = {}
    for tarefas in TAREFAS_POR_DIA.values():
        for tarefa in tarefas:
            cond = tarefa['condominio']
            if cond not in resumo_cond:
                resumo_cond[cond] = {'total': 0, 'valor': 0}
            resumo_cond[cond]['total'] += 1
            if tarefa.get('valor'):
                resumo_cond[cond]['valor'] += tarefa['valor']
    
    df_resumo = pd.DataFrame([
        {
            'Condomínio': cond,
            'Total Tarefas': dados['total'],
            'Valor Total': f"R$ {dados['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if dados['valor'] > 0 else "-"
        }
        for cond, dados in sorted(resumo_cond.items(), key=lambda x: x[1]['total'], reverse=True)
    ])
    
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🏢 <strong>Comprimóveis - Consultoria & Administração</strong></p>
    <p>Sistema BPO desenvolvido por Lucas | CRECI: 37215</p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">
        📞 (21) 3933-4137 | (21) 2421-3375 | WhatsApp: (21) 99372-1324
    </p>
</div>
""", unsafe_allow_html=True)
