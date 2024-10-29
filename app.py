import os
from dotenv import load_dotenv
import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    # Define the JSON schema for the response
    json_schema = {
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

    messages = [
        {"role": "system", "content": "You are a travel assistant. Extract travel information from the user's input and update the travel parameters accordingly."},
        {"role": "user", "content": f"Current travel parameters: {json.dumps(current_params)}"},
        {"role": "user", "content": f"User input: {user_input}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format={"type": "json_schema", "json_schema": json_schema}
    )
    print(response.choices[0].message)
    updated_params = json.loads(response.choices[0].message.parsed)
    
    # Merge updated params with current params
    for key, value in updated_params.items():
        if value is not None:
            current_params[key] = value
    return current_params

def generate_response(travel_params):
    messages = [
        {"role": "system", "content": "You are a helpful travel assistant. Respond to the user based on the current travel parameters."},
        {"role": "user", "content": f"Current travel parameters: {json.dumps(travel_params)}. Provide a friendly summary of the current travel plans and ask for any missing information."}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=150
    )

    return response.choices[0].message.content

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
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        interaction_mode = option_menu("Interaction Mode", ["Text", "Voice"], icons=["chat", "mic"], default_index=0, orientation="horizontal")

        if interaction_mode == "Text":
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if user_input := st.chat_input("What are your travel plans?"):
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)

                st.session_state.travel_params = process_travel_input(user_input, st.session_state.travel_params)
                
                response = generate_response(st.session_state.travel_params)
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)

            # Display current travel parameters
            st.sidebar.write("Current Travel Parameters:")
            for key, value in st.session_state.travel_params.items():
                st.sidebar.write(f"{key}: {value}")

            # Check if all necessary parameters are filled
            necessary_params = ["destination_airport", "departure_date"]
            if st.session_state.travel_params["round_trip"]:
                necessary_params.append("return_date")

            if all(st.session_state.travel_params[param] for param in necessary_params):
                if st.sidebar.button("Book Flight"):
                    st.sidebar.success("Flight booked successfully!")
            else:
                st.sidebar.warning("Please provide all necessary information to book your flight.")

        else:
            _, col22, _ = st.columns([5, 1, 5])
            with col22:
                audio = audiorecorder("", "")
                if len(audio) > 0:
                    #user_input = get_transcription(audio)
                    pass


# def get_transcription(file_path):
#     client = OpenAI()
#     audio_file = open(file_path, "rb")
#     transcription = client.audio.transcriptions.create(
#         model="whisper-1", 
#         file=audio_file
#     )
#     return transcription.text

if __name__ == "__main__":
    main()
