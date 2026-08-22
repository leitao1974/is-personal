import streamlit as st
from google import genai
from google.genai import types

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

# Inicializa o cliente do novo SDK oficial
client = genai.Client(api_key=gemini_api_key)

# Barra lateral
with st.sidebar:
    st.header("Configurações")
    selected_model = st.selectbox(
        "Selecione o Modelo:",
        options=[
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash"
        ],
        index=0
    )
    
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

# Processamento do prompt
if prompt := st.chat_input("Faça uma pergunta com pesquisa em tempo real..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_box = st.empty()
        
        try:
            # Configura a ferramenta Google Search
            tools = [types.Tool(google_search=types.GoogleSearch())] if enable_web_search else []
            config = types.GenerateContentConfig(
                tools=tools,
                temperature=0.7
            )

            # Formata histórico no padrão Content
            contents = []
            for m in st.session_state.messages:
                contents.append(
                    types.Content(
                        role=m["role"],
                        parts=[types.Part.from_text(text=m["content"])]
                    )
                )

            with st.spinner("A pesquisar na web e a gerar resposta..."):
                response = client.models.generate_content(
                    model=selected_model,
                    contents=contents,
                    config=config
                )
                full_text = response.text

            response_box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

        except Exception as e:
            response_box.error(f"Erro: {e}")
