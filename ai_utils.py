from typing import Dict, Any, Optional
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
from models import FlightParams, AIResponse
import json
from datetime import datetime
import pytz
import re
load_dotenv()

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FLIGHT_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "departure_id": {
            "type": "string (IATA code)",
            "description": "Airport code for departure (e.g., 'CDG')",
            "pattern": "^[A-Z]{3}$"
        },
        "arrival_id": {
            "type": "string (IATA code)",
            "description": "Airport code for arrival (e.g., 'AUS')",
            "pattern": "^[A-Z]{3}$"
        },
        "trip_type": {
            "type": "integer",
            "enum": [1, 2],
            "description": "1 for round trip, 2 for one way"
        },
        "outbound_date": {
            "type": "string (YYYY-MM-DD)",
            "format": "date",
            "description": "Departure date in YYYY-MM-DD format"
        },
        "return_date": {
            "type": "string (YYYY-MM-DD)",
            "format": "date",
            "description": "Return date in YYYY-MM-DD format (required if trip_type is 1)"
        },
        "adults": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of adult passengers"
        },
        "travel_class": {
            "type": "integer",
            "enum": [1, 2, 3, 4],
            "description": "1=Economy, 2=Premium Economy, 3=Business, 4=First"
        },
        "message": {
            "type": "string",
            "description": "Message to prompt the user for missing information. Null if no missing information."
        },
        "completion": {
            "type": "boolean",
            "description": "Indicates whether all required parameters are filled"
        },
        "outbound_times": {
            "type": "string",
            "description": "Comma-separated time ranges for outbound flight (e.g., '4,18,3,19' for 4AM-6PM departure, 3AM-7PM arrival)",
            "pattern": "^\\d{1,2}(,\\d{1,2}){1,3}$"
        },
        "return_times": {
            "type": "string",
            "description": "Comma-separated time ranges for return flight (e.g., '4,18,3,19' for 4AM-6PM departure, 3AM-7PM arrival)",
            "pattern": "^\\d{1,2}(,\\d{1,2}){1,3}$"
        }
    },
    "required": ["completion"],
    "additionalProperties": False
}


def load_system_prompt() -> str:
    """Load the system prompt from booking_prompt.json"""
    try:
        with open("booking_prompt.json", "r") as f:
            prompt_data = json.load(f)
            #get current date, time, day
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_day = datetime.now().strftime("%A")
            prepend = f"Today's date is {current_date} and the day of the week is {current_day}."
            return prepend + prompt_data["booking loop prompt"]
    except Exception as e:
        print(f"Error loading system prompt: {str(e)}")
        raise


def get_model_response(
    prompt: str, 
    current_params: FlightParams
) -> AIResponse:
    """
    Get structured response from OpenAI using JSON mode.
    """
    try:
        # Load the system prompt
        system_prompt = load_system_prompt()
        
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Current parameters: {current_params.json()}\nUser input: {prompt}"
                }
            ]
        )
        
        # Parse the response and ensure it's valid
        content = response.choices[0].message.content
        print(f"Debug - AI Response content: {content}")  # Add debug logging
        
        parsed_response = json.loads(content)
        return AIResponse(**parsed_response)

    except Exception as e:
        print(f"Error getting model response: {str(e)}")
        # Return a default AIResponse instead of None
        return AIResponse(
            message="I'm sorry, I encountered an error processing your request. Could you please rephrase that?",
            completion=False,
            adults=1,  # Keep existing parameters
            travel_class=1
        )


def parse_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts JSON from the model's response text.

    Args:
        text: The raw text response from the model.

    Returns:
        A dictionary representing the parsed JSON.
    """


    if not any(char in text for char in "{["):
        return {
            "message": text.strip(),
            "completion": False
        }

    try:
        # Pattern 1: JSON with code block markers
        json_patterns = [
            r"```json\s*(\{.*?\})\s*```",  # JSON code block
            r"```\s*(\{.*?\})\s*```",      # Generic code block
            r"\{.*?\}"                      # Raw JSON
        ]

        for pattern in json_patterns:
            matches = re.search(pattern, text, re.DOTALL)
            if matches:
                if pattern.startswith(r"\{"):
                    json_str = matches.group(0)  # Use entire match for raw JSON
                else:
                    json_str = matches.group(1)  # Use capture group for code blocks
                
                json_str = json_str.strip()
                return json.loads(json_str)

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {str(e)}")
        return


def update_parameters(
    current_params: FlightParams, 
    ai_response: AIResponse
) -> FlightParams:
    """
    Update current parameters with new values from AI response.
    """
    update_data = ai_response.dict(exclude_unset=True)
    # Remove only 'message' as we need to keep 'completion'
    update_data.pop("message", None)
    # Keep the completion status from the AI response
    updated_params = current_params.copy(update=update_data)
    return updated_params


def get_next_message(params: FlightParams, ai_response: AIResponse) -> Optional[str]:
    """
    Retrieve the message from AI response to prompt the user.

    Args:
        params: Current FlightParams instance
        ai_response: AIResponse object with updated parameters and message

    Returns:
        A string message to prompt the user, or None if booking is complete
    """
    if ai_response.completion:
        return None
    return ai_response.message


def run_booking_loop(initial_prompt: str = "I want to book a flight.") -> FlightParams:
    """
    Run the main booking loop until all parameters are collected.

    Args:
        initial_prompt: Initial user input

    Returns:
        Completed FlightParams instance
    """
    current_params = FlightParams()
    user_input = initial_prompt

    while not current_params.completion:
        ai_response = get_model_response(user_input, current_params)

        if not ai_response:
            print("Failed to get a valid response from the AI.")
            break
        # Update parameters with AI response
        try:
            current_params = update_parameters(current_params, ai_response)
        except Exception as e:
            print(f"Error updating parameters: {str(e)}")
            break

        # Check if booking is complete
        if ai_response.completion:
            print("All parameters collected. Ready to search for flights.")
            break
        else:
            # Get the message from AI to prompt the user
            message = get_next_message(current_params, ai_response)
            if message:
                print(f"Bot: {message}")
                user_input = input("User: ")
                if user_input.lower() in ["quit", "exit"]:
                    print("Booking process terminated by user.")
                    break
            else:
                print("Bot: Awaiting further information.")
                user_input = input("User: ")
                if user_input.lower() in ["quit", "exit"]:
                    print("Booking process terminated by user.")
                    break

    return current_params
