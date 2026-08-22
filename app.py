import streamlit as st
import json
import os
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Gemini Assistant - Análise de Ficheiros",
    page_icon="📂",
    layout="centered"
)

st.title("📂 Assistente Multimodal (Ficheiros, Memória & Busca)")

# Configuração da API Key
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

client = genai.Client(api_key=gemini_api_key)

MEMORY_FILE = "memory.json"

# Funções de gestão de memória permanente
def load_memories():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memories(memories_list):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories_list, f, ensure_ascii=False, indent=2)

if "persistent_memory" not in st.session_state:
    st.session_state.persistent_memory = load_memories()

# Barra lateral: Configurações, Carregamento de Ficheiros e Memória
with st.sidebar:
    st.header("⚙️ Configurações")
    selected_model = st.selectbox(
        "Modelo:",
        options=[
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash"
        ],
        index=0
    )
    
    enable_web_search = st.toggle("🌐 Ativar Google Search", value=True)
    enable_memory = st.toggle("🧠 Usar Memória de Longo Prazo", value=True)
    
    st.divider()
    st.header("📄 Carregar Ficheiro para Análise")
    uploaded_file = st.file_uploader(
        "Selecione um PDF, imagem ou texto:",
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv", "md"]
    )
    
    if uploaded_file is not None:
        st.success(f"Anexado: {uploaded_file.name}")

    st.divider()
    st.header("🧠 Memória Permanente")
    new_fact = st.text_input("Adicionar nota à memória:")
    if st.button("Guardar Nota") and new_fact:
        st.session_state.persistent_memory.append(new_fact)
        save_memories(st.session_state.persistent_memory)
        st.success("Nota guardada!")
        st.rerun()

    if st.session_state.persistent_memory:
        st.caption("Factos memorizados:")
        for item in st.session_state.persistent_memory:
            st.markdown(f"- {item}")
        if st.button("🗑️ Limpar Toda a Memória"):
            st.session_state.persistent_memory = []
            save_memories([])
            st.rerun()

    st.divider()
    if st.button("Limpar Conversa Atual"):
        st.session_state.messages = []
        st.rerun()

# Inicialização do histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do histórico de mensagens no ecrã
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Processamento do prompt
if prompt := st.chat_input("Faça uma pergunta sobre o ficheiro ou tema geral..."):
    # Mensagem apresentada na interface
    display_prompt = f"📎 *[Ficheiro: {uploaded_file.name}]*\n\n{prompt}" if uploaded_file else prompt
    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user"):
        st.markdown(display_prompt)

    with st.chat_message("assistant"):
        response_box = st.empty()
        
        try:
            # Instrução de sistema com memória persistente
            system_instruction_text = (
                "És um assistente analítico rigoroso, adaptativo e focado em detalhe técnico.\n"
            )
            if enable_memory and st.session_state.persistent_memory:
                memories_str = "\n".join(f"- {m}" for m in st.session_state.persistent_memory)
                system_instruction_text += (
                    f"\n[MEMÓRIA DE LONGO PRAZO]:\n{memories_str}\n"
                    "Utiliza estes factos como diretrizes operacionais de fundo."
                )

            tools = [types.Tool(google_search=types.GoogleSearch())] if enable_web_search else []
            config = types.GenerateContentConfig(
                system_instruction=system_instruction_text,
                tools=tools,
                temperature=0.4
            )

            # Prepara os blocos de conteúdo da conversa
            contents = []
            
            # Adiciona o histórico textual anterior
            for m in st.session_state.messages[:-1]:
                contents.append(
                    types.Content(
                        role=m["role"],
                        parts=[types.Part.from_text(text=m["content"])]
                    )
                )

            # Prepara a última mensagem com anexação direta de bytes (se existir ficheiro)
            current_parts = []
            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                current_parts.append(
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=uploaded_file.type
                    )
                )
            
            current_parts.append(types.Part.from_text(text=prompt))
            contents.append(types.Content(role="user", parts=current_parts))

            with st.spinner("A analisar conteúdo e a gerar resposta..."):
                response = client.models.generate_content(
                    model=selected_model,
                    contents=contents,
                    config=config
                )
                full_text = response.text

            response_box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            # Auto-memorização se detetar comandos específicos
            lower_prompt = prompt.lower()
            if any(k in lower_prompt for k in ["lembra-te de", "guarda na memória", "aprende que", "memoriza"]):
                st.session_state.persistent_memory.append(prompt)
                save_memories(st.session_state.persistent_memory)

        except Exception as e:
            response_box.error(f"Erro: {e}")
