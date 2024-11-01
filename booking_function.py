from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration constants
MAX_FLIGHTS_TO_RETURN = 5
SKYTEAM_AIRLINES = "SKYTEAM"

def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    trip_type: int = 1,  # 1=round trip, 2=one way
    return_date: Optional[str] = None,
    adults: int = 1,
    travel_class: int = 1,  # 1=Economy default
    api_key: str = "your_api_key_here",
) -> List[Dict[str, Any]]:
    """
    Search for SkyTeam flights using SerpAPI's Google Flights wrapper.

    Args:
        departure_id: Airport code for departure (e.g., "CDG")
        arrival_id: Airport code for arrival (e.g., "AUS")
        outbound_date: Departure date in YYYY-MM-DD format
        trip_type: 1 for round trip, 2 for one way
        return_date: Return date in YYYY-MM-DD format (required if trip_type=1)
        adults: Number of adult passengers
        travel_class: 1=Economy, 2=Premium economy, 3=Business, 4=First
        api_key: SerpAPI key

    Returns:
        List of top flights based on MAX_FLIGHTS_TO_RETURN
    """
    # Validate round trip parameters
    if trip_type == 1 and not return_date:
        raise ValueError("Return date is required for round trip flights")

    # Validate dates format and logic
    try:
        outbound = datetime.strptime(outbound_date, "%Y-%m-%d")
        if return_date:
            return_dt = datetime.strptime(return_date, "%Y-%m-%d")
            if return_dt < outbound:
                raise ValueError("Return date cannot be before departure date")
    except ValueError as e:
        raise ValueError("Invalid date format. Use YYYY-MM-DD") from e

    # Construct SerpAPI parameters
    params = {
        "engine": "google_flights",
        "departure_id": departure_id.upper(),
        "arrival_id": arrival_id.upper(),
        "outbound_date": outbound_date,
        "hl": "en",
        "adults": adults,
        "travel_class": travel_class,
        "include_airlines": "SKYTEAM",
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "type": 1,
    }
    
    # Add return date if round trip
    if trip_type == 1:
        params["return_date"] = return_date
    else:
        params["type"] = 2
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        # Consolidate flights into a single list
        all_flights = []
        # Add best flights if available
        best_flights = results.get("best_flights", [])
        all_flights.extend(best_flights)

        # Add other flights if needed to reach MAX_FLIGHTS_TO_RETURN
        if len(all_flights) < MAX_FLIGHTS_TO_RETURN:
            other_flights = results.get("other_flights", [])
            remaining_slots = MAX_FLIGHTS_TO_RETURN - len(all_flights)
            all_flights.extend(other_flights[:remaining_slots])
        # Return at most MAX_FLIGHTS_TO_RETURN flights
        return all_flights[:MAX_FLIGHTS_TO_RETURN]
    except Exception as e:
        raise RuntimeError(f"Flight search failed: {str(e)}") from e
