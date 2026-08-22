import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Gemini Free Assistant", page_icon="✨", layout="centered")
st.title("✨ Assistente Inteligente (Gemini Gratuito)")

# Configuração da API Key
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

genai.configure(api_key=gemini_api_key)

# Barra lateral
with st.sidebar:
    st.header("Configurações")
    model_choice = st.selectbox(
        "Modelo:",
        ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0
    )
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Inicialização do histórico
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição das mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Processamento do prompt
if prompt := st.chat_input("Como posso ajudar hoje?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_box = st.empty()
        full_text = ""
        
        try:
            model = genai.GenerativeModel(model_choice)
            
            # Formata histórico no padrão da biblioteca do Google
            history_payload = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history_payload.append({"role": role, "parts": [m["content"]]})

            chat = model.start_chat(history=history_payload)
            response = chat.send_message(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    response_box.markdown(full_text + "▌")

            response_box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

        except Exception as e:
            response_box.error(f"Erro: {e}")
