import os
import streamlit as st
import requests
import pytz
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool

load_dotenv()

# UI
st.set_page_config(page_title="Sharky AI", page_icon="🦈")

# Streamlit Session State
SYSTEM_PROMPT = """You are Sharky — a witty, charismatic AI assistant who acts like a cool shark. You speak with ocean-themed flair and shark puns, but you are HIGHLY knowledgeable and always give detailed, accurate, helpful answers on ANY topic the user asks about (science, tech, history, coding, math, general knowledge — all fair game).

Rules:
- ALWAYS answer the user's question fully and with good detail. Never dodge or deflect a question just because it's not weather/time.
- Keep your shark personality and ocean metaphors, but don't let the persona get in the way of actual information.
- Use the 'get_current_weather' tool for any real-time weather queries. Never make up weather data.
- Use the 'get_current_time' tool for current time queries.
- For everything else: answer directly, be informative, and sprinkle in Sharky's personality naturally."""

if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]

with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Elements: Streamlit + LangChain + Gemini")
    st.badge(f"📊 **Chat Depth:** {len(st.session_state.messages)} messages", color="blue")
    
    selected_model = st.selectbox(
        "Model",
        ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )
    
    # Creativity (Temperature) Slider
    temp = st.slider("Creativity (temperature)", 0.0, 1.0, 0.7)

    language_options = ("English", "Hindi", "Kannada")

    selected_language = st.radio(
        "**Response Language**", 
        language_options, 
        help="Under development! Sharky is expanding his vocabulary."
    )

    st.status(
        "OpenWeatherMap API ⛅", state="complete"
    )
    st.metric("Gemini API", "⚡ Active", delta="12ms Latency", delta_color="normal")
    st.checkbox("Show advanced settings", value=False, disabled=False, help="More settings coming soon!")
    st.divider()
    
    # Clear Chat
    if st.button("🌊 Drain", use_container_width=True):
        st.session_state.messages = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]
        st.rerun()

st.title("Where to, Captain? 🌩️")
st.caption("Sharky AI: Real-time global weather intelligence.")

@tool
def get_current_weather(city: str) -> str:
    """Get the current weather for a specific city."""
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            data = res.json()
            return f"{data['weather'][0]['description']}, {data['main']['temp']}°C"
        return f"Error: {res.status_code}"
    except Exception as e:
        return str(e)

@tool
def get_current_time(timezone: str = "Asia/Kolkata") -> str:
    """
    Get the current time for a specific timezone. 
    Common inputs: 'Asia/Kolkata', 'America/New_York', 'UTC'.
    """
    try:
        tz = pytz.timezone(timezone)
        return datetime.now(tz).strftime("%I:%M %p (%Z) | %A, %B %d, %Y")
    except Exception:
        return datetime.now(pytz.utc).strftime("%I:%M %p (UTC) | %A, %B %d, %Y")

# Map tool names to the actual objects
tools_map = {"get_current_weather": get_current_weather, "get_current_time": get_current_time}

# Initialize Model with Tools 
llm = ChatGoogleGenerativeAI(model=selected_model, temperature=temp)
llm_with_tools = llm.bind_tools([get_current_weather, get_current_time])


def extract_text(content) -> str:
    """
    Safely extract a plain string from Gemini's response content,
    which may be a str, a list of dicts, or a single dict.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)

    if isinstance(content, dict):
        return content.get("text", "")

    return str(content)


# Display history
for msg in st.session_state.messages:
    if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
        if isinstance(msg, HumanMessage):
            role = "user"
            icon = "👨"
        else:
            role = "assistant"
            icon = "🦈"
            
        with st.chat_message(role, avatar=icon):
            # Always extract clean text before rendering
            st.markdown(extract_text(msg.content))


# MAIN
if prompt := st.chat_input("How is the weather in Tokyo?"):
    st.chat_message("user", avatar="🧑").markdown(prompt)
    st.session_state.messages.append(HumanMessage(content=prompt))

    with st.chat_message("assistant", avatar="🦈"):
        # LLM Call
        response = llm_with_tools.invoke(st.session_state.messages)
        st.session_state.messages.append(response)

        # For Tool Calls
        if response.tool_calls:
            for tool_call in response.tool_calls:
                with st.status("Refreshing the atmosphere...."):
                    tool_func = tools_map[tool_call["name"]]
                    tool_output = tool_func.invoke(tool_call["args"])

                    st.session_state.messages.append(
                        ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_call["id"]
                        )
                    )
                
                if tool_call["name"] == "get_current_weather":
                    display_text = f"Currently, in {tool_call['args']['city']}: it's **{tool_output}**"
                else:
                    display_text = f"Currently, in {tool_call['args'].get('timezone', 'India')} it's **{tool_output}**"

                # Typing effect
                msg_box = st.empty()
                typed = ""
                for ch in display_text:
                    typed += ch
                    msg_box.info(typed + "▌")
                    time.sleep(0.015)
                msg_box.info(display_text)

                st.session_state.messages.append(AIMessage(content=display_text))

        else:
            # Extract clean string ONCE before the typing loop
            full_response = extract_text(response.content)

            msg_box = st.empty()
            typed = ""
            for ch in full_response:
                typed += ch
                msg_box.markdown(typed + "▌")
                time.sleep(0.01)
            msg_box.markdown(typed)

            # Store clean string in history (not the raw list)
            st.session_state.messages[-1] = AIMessage(content=full_response)
