from typing import Dict, Any, Optional
import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
from models import FlightParams, AIResponse

load_dotenv()

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FLIGHT_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "departure_id": {
            "type": "string",
            "description": "Airport code for departure (e.g., 'CDG')",
            "pattern": "^[A-Z]{3}$"
        },
        "arrival_id": {
            "type": "string",
            "description": "Airport code for arrival (e.g., 'AUS')",
            "pattern": "^[A-Z]{3}$"
        },
        "trip_type": {
            "type": "integer",
            "enum": [1, 2],
            "description": "1 for round trip, 2 for one way"
        },
        "outbound_date": {
            "type": "string",
            "format": "date",
            "description": "Departure date in YYYY-MM-DD format"
        },
        "return_date": {
            "type": "string",
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
            "description": "Message to prompt the user for missing information"
        },
        "completion": {
            "type": "boolean",
            "description": "Indicates whether all required parameters are filled"
        }
    },
    "required": ["completion"],
    "additionalProperties": False
}


def get_model_response(
    prompt: str, 
    current_params: FlightParams
) -> AIResponse:
    """
    Get structured response from OpenAI using JSON mode.

    Args:
        prompt: User's input text
        current_params: Current state of flight parameters

    Returns:
        AIResponse object containing updated parameters, message, and completion flag
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant helping to collect flight booking parameters. "
                        "Analyze user input and current parameters to update the flight booking information. "
                        "Provide a message to the user requesting any missing information. "
                        "Set 'completion' to true only when all required parameters are properly filled. "
                        "Respond in JSON format adhering to the following schema:\n\n"
                        f"{FLIGHT_PARAMS_SCHEMA}"
                    )
                },
                {"role": "user", "content": prompt},
                {
                    "role": "assistant",
                    "content": f"Current parameters: {current_params.json()}"
                }
            ]
        )

        # Extract and parse the JSON response
        print(response)
        assistant_message = response.choices[0].message.content
        structured_response = parse_json_from_text(assistant_message)
        ai_response = AIResponse(**structured_response)
        return ai_response
    except Exception as e:
        print(f"Error communicating with OpenAI: {str(e)}")
        return AIResponse()


def parse_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts JSON from the model's response text.

    Args:
        text: The raw text response from the model.

    Returns:
        A dictionary representing the parsed JSON.
    """
    import json
    import re

    try:
        # Regex to find JSON block
        json_pattern = re.compile(r"```json\s*(\{.*\})\s*```", re.DOTALL)
        match = json_pattern.search(text)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            # Attempt to parse JSON without code block
            return json.loads(text)
    except json.JSONDecodeError:
        print("Failed to parse JSON from the response.")
        return {}


def update_parameters(
    current_params: FlightParams, 
    ai_response: AIResponse
) -> FlightParams:
    """
    Update current parameters with new values from AI response.

    Args:
        current_params: Current FlightParams instance
        ai_response: AIResponse object with updated parameters

    Returns:
        Updated FlightParams instance
    """
    update_data = ai_response.dict(exclude_unset=True)
    # Remove 'message' and 'completion' to avoid conflicts
    update_data.pop("message", None)
    update_data.pop("completion", None)
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
        print("hi1")
        ai_response = get_model_response(user_input, current_params)

        if not ai_response:
            print("Failed to get a valid response from the AI.")
            break
        print("hi2")
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
