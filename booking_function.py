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
    trip_type: int = 1,
    return_date: Optional[str] = None,
    adults: int = 1,
    travel_class: int = 1,
    outbound_times: Optional[str] = None,
    return_times: Optional[str] = None,
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
        outbound_times: Optional comma-separated time ranges for outbound flight
        return_times: Optional comma-separated time ranges for return flight
        api_key: SerpAPI key

    Returns:
        List of top flights based on MAX_FLIGHTS_TO_RETURN
    """
    # Validate round trip parameters
    if trip_type == 1 and not return_date:
        raise ValueError("Return date is required for round trip flights")

    # Construct base parameters
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
        "type": 2 if trip_type == 2 else 1
    }

    # Add return date for round trips
    if trip_type == 1:
        params["return_date"] = return_date
        
    # Add time preferences only if specified
    if outbound_times:
        params["outbound_times"] = outbound_times
    if return_times and trip_type == 1:
        params["return_times"] = return_times

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Consolidate and return flights
        all_flights = []
        all_flights.extend(results.get("best_flights", []))
        if len(all_flights) < MAX_FLIGHTS_TO_RETURN:
            other_flights = results.get("other_flights", [])
            remaining_slots = MAX_FLIGHTS_TO_RETURN - len(all_flights)
            all_flights.extend(other_flights[:remaining_slots])
        return all_flights[:MAX_FLIGHTS_TO_RETURN]
    except Exception as e:
        raise RuntimeError(f"Flight search failed: {str(e)}") from e
