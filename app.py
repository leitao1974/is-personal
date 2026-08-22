import streamlit as st
import google.generativeai as genai

st.set_page_config(
    page_title="Gemini Deep Search Assistant",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 Assistente com Deep Search (Web Grounding)")

# Configuração da API Key
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

genai.configure(api_key=gemini_api_key)

# Obtém dinamicamente os modelos de geração de texto ativos
@st.cache_data(ttl=3600)
def get_gemini_models():
    try:
        models = [
            m.name.replace("models/", "") 
            for m in genai.list_models() 
            if "generateContent" in m.supported_generation_methods
        ]
        return models if models else ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    except Exception:
        return ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

available_models = get_gemini_models()

# Barra lateral
with st.sidebar:
    st.header("Configurações")
    model_choice = st.selectbox(
        "Selecione o Modelo:",
        options=available_models,
        index=0
    )
    
    # Interruptor para ativar Pesquisa na Web / Deep Search
    enable_web_search = st.toggle("🌐 Ativar Google Search (Deep Search)", value=True)
    
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Inicialização do histórico
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do histórico de mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Processamento da entrada do utilizador
if prompt := st.chat_input("Faça uma pergunta com pesquisa em tempo real..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_box = st.empty()
        
        try:
            # Configura a ferramenta correta de Web Grounding para o SDK
            tools = [{"google_search_retrieval": {}}] if enable_web_search else None
            
            model = genai.GenerativeModel(
                model_name=model_choice,
                tools=tools
            )
            
            # Formata histórico no padrão da biblioteca do Google
            history_payload = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history_payload.append({"role": role, "parts": [m["content"]]})

            chat = model.start_chat(history=history_payload)
            
            # Com Grounding ativo, a geração completa garante a consolidação das fontes
            with st.spinner("A pesquisar na web e a gerar resposta..."):
                response = chat.send_message(prompt)
                full_text = response.text

            response_box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

        except Exception as e:
            response_box.error(f"Erro: {e}")
