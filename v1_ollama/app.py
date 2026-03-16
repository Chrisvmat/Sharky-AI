import streamlit as st
from ollama import chat # used to send messages to ollama models (interaction)

st.set_page_config(page_title="Sharky AI", page_icon="🦈")
st.title("Chat with Sharky 🦈")

# settings
st.sidebar.subheader("⚙️ Settings")

model = st.sidebar.selectbox(
    "Model",
    ["phi3:3.8b", "llama3.1:8b", "tinyllama"],
    index=0
)

temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.5, 0.7, 0.1)

if st.sidebar.button("🧹 Clear chat"):
    st.session_state.messages = []
    st.rerun()

# ---------- Chat history ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are Sharky, a friendly and slightly funny assistant. "
                "You explain things clearly and keep answers concise unless "
                "the user asks for more detail."
            )
        }
    ]

# Show previous messages (skip system)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Placeholder at bottom to help auto-scroll
bottom = st.empty()

# user input
if prompt := st.chat_input("Ask me anything!"):
    # Stores user message in history and displays it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # streaming assistant response
    full_response = ""
    with st.chat_message("assistant"):
        msg_box = st.empty()

        # Spinner while we stream
        with st.spinner("Generating response..."):
            for part in chat(
                model=model,
                messages=st.session_state.messages,
                stream=True,
                options={"temperature": temperature},
            ):
                token = part["message"]["content"]
                full_response += token

                # Blinking cursor effect
                msg_box.markdown(full_response + "▌")
                bottom.markdown(" ")  # keeps view pinned to bottom

        # Final message without cursor
        msg_box.markdown(full_response)

    # Save assistant message to history
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
