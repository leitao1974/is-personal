import streamlit as st
import json
import os
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Gemini Assistant com Memória Permanente",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Assistente com Memória & Deep Search")

# Configuração da API Key
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_api_key:
    st.error("Chave GEMINI_API_KEY não configurada nos Secrets.")
    st.stop()

client = genai.Client(api_key=gemini_api_key)

MEMORY_FILE = "memory.json"

# Funções para gestão do ficheiro de memória permanente
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

# Barra lateral: Configurações e Gestor de Memória
with st.sidebar:
    st.header("⚙️ Configurações")
    selected_model = st.selectbox(
        "Selecione o Modelo:",
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
    st.header("🧠 Memória Permanente")
    
    # Adicionar facto manualmente
    new_fact = st.text_input("Adicionar nota/instrução à memória:")
    if st.button("Guardar Nota") and new_fact:
        st.session_state.persistent_memory.append(new_fact)
        save_memories(st.session_state.persistent_memory)
        st.success("Nota guardada!")
        st.rerun()

    # Visualização de memórias guardadas
    if st.session_state.persistent_memory:
        st.caption("Conhecimento retido entre sessões:")
        for idx, item in enumerate(st.session_state.persistent_memory):
            st.markdown(f"- {item}")
        
        if st.button("🗑️ Limpar Toda a Memória"):
            st.session_state.persistent_memory = []
            save_memories([])
            st.success("Memória apagada.")
            st.rerun()
    else:
        st.caption("Ainda não há memórias permanentes guardadas.")

    st.divider()
    if st.button("Limpar Conversa Atual"):
        st.session_state.messages = []
        st.rerun()

# Inicialização do histórico da sessão ativa
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibição do histórico de mensagens no ecrã
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Processamento do prompt
if prompt := st.chat_input("Faça uma pergunta ou ensine algo novo à IA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_box = st.empty()
        
        try:
            # Constrói o System Instruction com a memória acumulada
            system_instruction_text = (
                "És um assistente altamente competente, rigoroso e adaptativo.\n"
            )
            
            if enable_memory and st.session_state.persistent_memory:
                memories_str = "\n".join(f"- {m}" for m in st.session_state.persistent_memory)
                system_instruction_text += (
                    f"\n[MEMÓRIA E FACTOS APRENDIDOS DE SESSÕES ANTERIORES]:\n{memories_str}\n"
                    "Utiliza obrigatoriamente estes factos de fundo para personalizar e orientar as tuas respostas."
                )

            # Configura ferramentas (Google Search) e instruções de sistema
            tools = [types.Tool(google_search=types.GoogleSearch())] if enable_web_search else []
            config = types.GenerateContentConfig(
                system_instruction=system_instruction_text,
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

            with st.spinner("A processar com memória e contexto..."):
                response = client.models.generate_content(
                    model=selected_model,
                    contents=contents,
                    config=config
                )
                full_text = response.text

            response_box.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            # Auto-aprendizagem opcional: se o utilizador disser explicitamente "lembra-te" ou "guarda na memória"
            lower_prompt = prompt.lower()
            if any(k in lower_prompt for k in ["lembra-te de", "guarda na memória", "aprende que", "memoriza"]):
                st.session_state.persistent_memory.append(prompt)
                save_memories(st.session_state.persistent_memory)

        except Exception as e:
            response_box.error(f"Erro: {e}")
