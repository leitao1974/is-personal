import streamlit as st
from groq import Groq

# Configuração da página
st.set_page_config(
    page_title="Chat Assistant - Groq",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Chat Assistant")

# Leitura da API Key a partir dos Segredos do Streamlit
groq_api_key = st.secrets.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("Chave 'GROQ_API_KEY' não configurada nos Secrets do Streamlit.")
    st.info("Aceda a Settings > Secrets na sua aplicação Streamlit e adicione: GROQ_API_KEY = 'gsk_...'")
    st.stop()

# Inicialização do cliente Groq
client = Groq(api_key=groq_api_key)

# Barra lateral para seleção de modelo e parâmetros
with st.sidebar:
    st.header("Configurações")
    selected_model = st.selectbox(
        "Selecione o Modelo:",
        options=[
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "deepseek-r1-distill-llama-70b",
            "mixtral-8x7b-32768"
        ],
        index=0
    )
    
    temperature = st.slider("Temperatura (Criatividade):", min_value=0.0, max_value=1.0, value=0.6, step=0.1)
    
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Inicialização do histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do histórico de mensagens no ecrã
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Caixa de entrada de texto
if prompt := st.chat_input("Escreva a sua mensagem..."):
    # Adiciona e apresenta a mensagem do utilizador
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geração da resposta da IA com streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")
                    
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            response_placeholder.error(f"Ocorreu um erro: {e}")
