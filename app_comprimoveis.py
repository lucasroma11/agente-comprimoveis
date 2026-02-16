"""
🏢 Interface Web - Agente Comprimóveis
Consultoria & Administração - "A chave do seu sonho está aqui"

Criado para: Ubirajara e Vanessa testarem
"""

import streamlit as st
import google.generativeai as genai
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Agente Comprimóveis",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para deixar bonito
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.95;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .bot-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CABEÇALHO
# ============================================================================

st.markdown("""
<div class="main-header">
    <h1>🏢 Agente Comprimóveis</h1>
    <p>Consultoria & Administração</p>
    <p style="font-size: 1rem; margin-top: 0.5rem;">"A chave do seu sonho está aqui"</p>
    <p style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.8;">CRECI: 37215 | Freguesia - RJ</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURAÇÃO DA API (SIDEBAR)
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuração")
    st.markdown("---")
    
    api_key = st.text_input(
        "API Key do Google Gemini:",
        type="password",
        help="Cole sua chave da API do Google aqui",
        placeholder="AIza..."
    )
    
    if api_key:
        st.success("✅ API Key configurada!")
    else:
        st.warning("⚠️ Insira a API Key para começar")
    
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
    
    if st.button("🔄 Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# ============================================================================
# CONTEXTO DO AGENTE
# ============================================================================

CONTEXTO = """Você é o assistente inteligente da Comprimóveis - Consultoria & Administração.
CRECI: 37215
Slogan: "A chave do seu sonho está aqui"

Localização: Estrada dos Três Rios, 1200 Sala 620, Freguesia - RJ
Telefones: (21) 3933-4137, (21) 2421-3375
WhatsApp: (21) 99372-1324

Você atua em: Freguesia (Jacarepaguá), Pechincha, Tanque, Tijuca e todo Rio de Janeiro.

Serviços principais:
- Compra e venda de imóveis
- Locação de imóveis
- Administração de condomínios (relatórios financeiros, RH, assessoria jurídica, contábil)
- Gestão de facilities

Equipe:
- Ubirajara: Dono e especialista em compra e vendas
- Vanessa: Dona, administradora e marketing
- Erick: Corretor
- Mais 2 corretores

Diferenciais:
- Transparência total (envio mensal de relatórios)
- Assessoria completa (trabalhista, jurídica, contábil)
- Sistema de gestão inovador
- Acompanhamento em assembleias

Seja profissional, prestativo e objetivo. Use emojis moderadamente para deixar a conversa agradável."""

# ============================================================================
# INICIALIZAÇÃO DO CHAT
# ============================================================================

# Inicializa histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensagem de boas-vindas
    st.session_state.messages.append({
        "role": "assistant",
        "content": """Olá! 👋 Bem-vindo à Comprimóveis!

Sou o assistente virtual da empresa. Como posso ajudá-lo(a) hoje?

💡 **Posso auxiliar com:**
- Informações sobre imóveis para venda ou locação
- Gestão de condomínios
- Assessoria imobiliária
- Dúvidas sobre nossos serviços

Fique à vontade para perguntar! 😊"""
    })

# ============================================================================
# EXIBIR HISTÓRICO DO CHAT
# ============================================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ============================================================================
# INPUT DO USUÁRIO
# ============================================================================

if prompt := st.chat_input("Digite sua mensagem aqui..."):
    
    # Verifica se API Key foi configurada
    if not api_key:
        st.error("⚠️ Por favor, configure a API Key no menu lateral antes de começar!")
        st.stop()
    
    # Adiciona mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Exibe mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Gera resposta do agente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Configura Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Monta histórico para contexto
            historico_texto = "\n\n".join([
                f"{'Usuário' if msg['role'] == 'user' else 'Você'}: {msg['content']}"
                for msg in st.session_state.messages[-6:]  # Últimas 3 interações
            ])
            
            # Monta prompt completo
            prompt_completo = f"""{CONTEXTO}

Histórico recente da conversa:
{historico_texto}

Usuário pergunta agora: {prompt}

Responda de forma profissional, prestativa e objetiva:"""
            
            # Gera resposta
            with st.spinner("Pensando..."):
                response = model.generate_content(prompt_completo)
                resposta_texto = response.text
            
            # Exibe resposta
            message_placeholder.markdown(resposta_texto)
            
            # Adiciona resposta ao histórico
            st.session_state.messages.append({
                "role": "assistant",
                "content": resposta_texto
            })
            
        except Exception as e:
            erro_msg = f"❌ **Erro:** {str(e)}\n\n"
            
            if "API_KEY_INVALID" in str(e) or "not valid" in str(e):
                erro_msg += "💡 Sua API Key parece estar incorreta. Verifique no menu lateral."
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                erro_msg += "⚠️ Limite de uso da API atingido. Aguarde alguns minutos ou tente amanhã."
            else:
                erro_msg += "💡 Tente reformular sua pergunta ou verifique sua conexão."
            
            message_placeholder.markdown(erro_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": erro_msg
            })

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🏢 <strong>Comprimóveis - Consultoria & Administração</strong></p>
    <p>Desenvolvido com ❤️ por Lucas | Agente IA em fase de testes</p>
</div>
""", unsafe_allow_html=True)
