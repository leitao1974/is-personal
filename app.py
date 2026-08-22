import streamlit as st
from groq import Groq

st.set_page_config(page_title="LLM Grátis na Nuvem", page_icon="⚡", layout="centered")
st.title("Chat com Llama 3.3 70B (Via Groq)")

# Lê a API Key guardada nos Segredos do Streamlit
groq_api_key = st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("Chave GROQ_API_KEY não configurada nos segredos.")
    st.stop()

client = Groq(api_key=groq_api_key)

# Inicializa o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra histórico na interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Processa novo prompt
if prompt := st.chat_input("Escreva uma mensagem..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_text = ""
        
        # Chamada com streaming para resposta instantânea
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            temperature=0.6,
            stream=True,
        )
        
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_text += content
                response_placeholder.markdown(full_text + "▌")
                
        response_placeholder.markdown(full_text)

    st.session_state.messages.append({"role": "assistant", "content": full_text})