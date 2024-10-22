import os
from dotenv import load_dotenv
import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from audiorecorder import audiorecorder
from swarm import Swarm, Agent
import json

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = Swarm()

DEFAULT_PARAMS = {
    "source_airport": "ATL",
    "destination_airport": None,
    "departure_date": None,
    "return_date": None,
    "round_trip": True,
    "num_passengers": 1,
    "class_of_travel": "economy"
}

def process_travel_input(user_input, current_params):
    function_description = {
        "name": "update_travel_params",
        "description": "Update travel parameters based on user input",
        "parameters": {
            "type": "object",
            "properties": {
                "destination_airport": {"type": "string"},
                "departure_date": {"type": "string", "format": "date"},
                "return_date": {"type": "string", "format": "date"},
                "round_trip": {"type": "boolean"},
                "num_passengers": {"type": "integer", "minimum": 1},
                "class_of_travel": {"type": "string", "enum": ["economy", "business", "first"]}
            }
        }
    }

    messages = [
        {"role": "system", "content": "You are a travel assistant. Extract travel information from the user's input and update the travel parameters accordingly."},
        {"role": "user", "content": f"Current travel parameters: {json.dumps(current_params)}"},
        {"role": "user", "content": f"User input: {user_input}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        functions=[function_description],
        function_call={"name": "update_travel_params"}
    )

    updated_params = json.loads(response.choices[0].function_call.arguments)
    
    # Merge updated params with current params
    for key, value in updated_params.items():
        if value is not None:
            current_params[key] = value

    return current_params

travel_agent = Agent(
    name="Travel Agent",
    instructions="""You are a helpful travel agent. Your job is to assist users in booking flights.
    Always check if all necessary information is provided before attempting to book a flight.
    If information is missing, ask the user politely for the missing details.""",
    functions=[process_travel_input]
)

def main():
    
    st.set_page_config(
        page_title="Tailwind",
        page_icon=":material/travel:",
        layout="wide",
    )
    
    st.markdown("""<h1 style="text-align: center; font-weight: bold;">Tailwind</h1>""", unsafe_allow_html=True)
    st.write("""<h4 style="text-align: center;">A Buddy for Your Next Trip</h4>""", unsafe_allow_html=True)
    
    if 'travel_params' not in st.session_state:
        st.session_state.travel_params = DEFAULT_PARAMS.copy()
    
    
        
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        interaction_mode = option_menu("Interaction Mode", ["Text", "Voice"], default_index=0, orientation="horizontal")

        if interaction_mode == "Text":
            user_input = st.text_input("**Where are we going today?**", "", label_visibility="hidden", placeholder="Take me to Paris next Friday")
        else:
            _, col22, _ = st.columns([5, 1, 5])
            with col22:
                audio = audiorecorder("", "")
                if len(audio) > 0:
                    #user_input = get_transcription(audio)
                    pass


def get_transcription(file_path):
    client = OpenAI()
    audio_file = open(file_path, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcription.text

if __name__ == "__main__":
    main()
