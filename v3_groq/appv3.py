import os
import streamlit as st
import requests
import pytz
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool

load_dotenv()

# UI
st.set_page_config(page_title="Sharky AI", page_icon="🦈")

# Streamlit Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="You are Sharky, a helpful and witty assistant. ACT as a cool Shark. Use the 'get_current_weather' tool for any questions about weather. Do not provide generic or fake weather info. Use the 'get_current_time' tool for time-related queries.")
    ]

with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Elements: Streamlit + LangChain + Groq")
    st.badge(f"📊 **Chat Depth:** {len(st.session_state.messages)} messages", color="blue")
    
    selected_model = st.selectbox(
        "Model",
        ["llama-3.1-8b-instant", "phi3:3.8b", "tinyllama"],
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
    st.metric("Groq API", "⚡ Active", delta="12ms Latency", delta_color="normal")
    st.checkbox("Show advanced settings", value=False, disabled=False, help="More settings coming soon!")
    st.divider()
    
    # Clear Chat
    if st.button("🌊 Drain", use_container_width=True):
        st.session_state.messages = [
            SystemMessage(content="You are Sharky, a helpful and witty assistant. Use tools for weather.")
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
        return datetime.now(tz).strftime("%I:%M %p (%Z)")
    except Exception:
        # Excep: UTC if timezone is invalid
        return datetime.now(pytz.utc).strftime("%I:%M %p (UTC)")

# Map tool names to the actual objects
tools_map = {"get_current_weather": get_current_weather, "get_current_time": get_current_time}

# Initialize Model with Tools 
llm = ChatGroq(model=selected_model, temperature=temp)
llm_with_tools = llm.bind_tools([get_current_weather, get_current_time])

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
            st.markdown(msg.content)

# Chat Logic
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
                    # Use .invoke() to avoid the StructuredTool error
                    tool_output = tool_func.invoke(tool_call["args"])

                    st.session_state.messages.append(
                        ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_call["id"]
                        )
                    )
                
                if tool_call["name"] == "get_current_weather":
                    display_text = f"Currently in {tool_call['args']['city']}: it's **{tool_output}**"
                else:
                    display_text = f"Time now, in {tool_call['args'].get('timezone', 'India')} is **{tool_output}**"

                # Simulating typing effect
                msg_box = st.empty()
                typed = ""
                for ch in display_text:
                    typed += ch
                    msg_box.info(typed + "▌")
                    time.sleep(0.015)
                msg_box.info(display_text)

                st.session_state.messages.append(AIMessage(content=display_text))

        else:
            # If no tool was needed, show the direct response
            full_response = response.content
            msg_box = st.empty()
            typed = ""
            for ch in full_response:
                typed += ch
                msg_box.markdown(typed + "▌")
                time.sleep(0.01)
            msg_box.markdown(full_response)
