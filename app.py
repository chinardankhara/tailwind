import os
from dotenv import load_dotenv
import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

#TODO: Change this to actual schema. These are example values.
DEFAULT_PARAMS = {
    "source_airport": "ATL",
    "round_trip_status": True,
    "num_passengers": 1,
    "class_of_travel": "economy"
}

def main():
    # Set the page configuration
    st.set_page_config(
        page_title="Tailwind",
        page_icon=":material/travel:",
        layout="wide",
    )

    # Title, Centered, Bolded
    st.markdown("""<h1 style="text-align: center; font-weight: bold;">Tailwind</h1>""", unsafe_allow_html=True)
    st.write("""<h4 style="text-align: center;">A Buddy for Your Next Trip</h4>""", unsafe_allow_html=True)

    # Center the input elements using columns
    _, col2, col3 = st.columns([1, 2, 1])
    
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful travel assistant. Ask for any missing information needed to plan a trip. The source airport is always ATL."}
        ]
    if 'travel_params' not in st.session_state:
        st.session_state.travel_params = DEFAULT_PARAMS.copy()

    with col2:
        # Natural Language Query Input
        user_input = st.text_input("**Where are we going today?**", "", label_visibility="hidden", placeholder="Take me to Paris next Friday")

    with col3: 
        audio = audiorecorder("", "")
        file_path = "recordings/audio.mp3"
        audio.export(file_path, "mp3")
        transcription = get_transcription(file_path)
        os.remove(file_path)
    # Display the entered input (Placeholder for processing)
    if user_input:
        st.success("Processing your request...")

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
