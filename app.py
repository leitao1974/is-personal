import streamlit as st
import json
import os
import re
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Gemini Assistant - Análise Documental",
    page_icon="📂",
    layout="centered"
)

st.title("📂 Assistente de Análise Documental")

# Configuração da API Key
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

client = genai.Client(api_key=gemini_api_key)

MEMORY_FILE = "memory.json"

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

# Função para filtrar citações redundantes da API
def clean_citation_tags(text: str) -> str:
    # Remove padrões como ou [citation: ...]
    cleaned = re.sub(r'\+\]', '', text)
    cleaned = re.sub(r'\[citation:\s*[\d,\s]+\]', '', cleaned)
    return cleaned

# Barra lateral
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
    
    enable_web_search = st.toggle("🌐 Ativar Google Search (Deep Search)", value=False)
    enable_memory = st.toggle("🧠 Usar Memória de Longo Prazo", value=True)
    
    st.divider()
    st.header("📄 Carregar Ficheiros")
    uploaded_files = st.file_uploader(
        "Selecione ficheiros (PDF, imagens, txt):",
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv", "md"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} ficheiro(s) carregado(s):")
        for f in uploaded_files:
            st.caption(f"• {f.name}")

    st.divider()
    st.header("🧠 Memória Permanente")
    new_fact = st.text_input("Adicionar nota:")
    if st.button("Guardar Nota") and new_fact:
        st.session_state.persistent_memory.append(new_fact)
        save_memories(st.session_state.persistent_memory)
        st.success("Guardado!")
        st.rerun()

    if st.session_state.persistent_memory:
        for item in st.session_state.persistent_memory:
            st.markdown(f"- {item}")
        if st.button("🗑️ Limpar Toda a Memória"):
            st.session_state.persistent_memory = []
            save_memories([])
            st.rerun()

    st.divider()
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# Histórico da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada do utilizador
if prompt := st.chat_input("Faça uma pergunta sobre o documento..."):
    display_prompt = f"📎 *[Anexos: {', '.join([f.name for f in uploaded_files])}]*\n\n{prompt}" if uploaded_files else prompt
    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user"):
        st.markdown(display_prompt)

    with st.chat_message("assistant"):
        response_box = st.empty()
        
        try:
            # Instrução de sistema otimizada para análise técnica sem lixo de formatação
            system_instruction_text = (
                "És um assistente técnico e analítico de alto nível. "
                "Ao analisar documentos anexados, sê objetivo, rigoroso e estruturado. "
                "NÃO incluas tags de citação inline ou índices numéricos automáticos no texto corrido (como).\n"
            )
            
            if enable_memory and st.session_state.persistent_memory:
                memories_str = "\n".join(f"- {m}" for m in st.session_state.persistent_memory)
                system_instruction_text += f"\n[MEMÓRIA PERMANENTE]:\n{memories_str}\n"

            # Se houver ficheiros anexados, desativa o Search temporariamente para não poluir
            use_search = enable_web_search and not uploaded_files
            tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else []

            config = types.GenerateContentConfig(
                system_instruction=system_instruction_text,
                tools=tools,
                temperature=0.2
            )

            contents = []
            for m in st.session_state.messages[:-1]:
                contents.append(
                    types.Content(
                        role=m["role"],
                        parts=[types.Part.from_text(text=m["content"])]
                    )
                )

            current_parts = []
            if uploaded_files:
                for f in uploaded_files:
                    file_bytes = f.getvalue()
                    current_parts.append(
                        types.Part.from_bytes(
                            data=file_bytes,
                            mime_type=f.type
                        )
                    )
            
            current_parts.append(types.Part.from_text(text=prompt))
            contents.append(types.Content(role="user", parts=current_parts))

            with st.spinner("A processar e a estruturar a análise..."):
                response = client.models.generate_content(
                    model=selected_model,
                    contents=contents,
                    config=config
                )
                full_text = clean_citation_tags(response.text)

            response_box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            lower_prompt = prompt.lower()
            if any(k in lower_prompt for k in ["lembra-te de", "guarda na memória", "aprende que", "memoriza"]):
                st.session_state.persistent_memory.append(prompt)
                save_memories(st.session_state.persistent_memory)

        except Exception as e:
            response_box.error(f"Erro: {e}")
