from typing import List, Dict, Any, Optional, Tuple, Union
from serpapi import GoogleSearch
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration constants
MAX_FLIGHTS_TO_RETURN = 5
SKYTEAM_AIRLINES = "SKYTEAM"

FlightResult = Union[List[Dict[str, Any]], List[Tuple[Dict[str, Any], Dict[str, Any]]]]

def search_outbound_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    travel_class: int = 1,
    outbound_times: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for outbound flights."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY not found in environment variables")
        
    params = {
        "engine": "google_flights",
        "departure_id": departure_id.upper(),
        "arrival_id": arrival_id.upper(),
        "outbound_date": outbound_date,
        "hl": "en",
        "adults": adults,
        "travel_class": travel_class,
        "include_airlines": SKYTEAM_AIRLINES,
        "api_key": api_key,
        "type": "1"
    }
    
    if return_date:
        params["return_date"] = return_date
        
    if outbound_times:
        params["outbound_times"] = outbound_times

    print(f"Debug: Outbound search params: {params}")
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        print(f"Debug: Raw API response: {results}")
        
        all_flights = []
        best_flights = results.get("best_flights", [])
        print(f"Debug: Best flights found: {len(best_flights)}")
        
        all_flights.extend(best_flights)
        return all_flights[:MAX_FLIGHTS_TO_RETURN]
    except Exception as e:
        print(f"Debug: Search failed with error: {str(e)}")
        raise RuntimeError(f"Outbound flight search failed: {str(e)}") from e

def search_return_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,
    departure_token: str,
    adults: int = 1,
    travel_class: int = 1,
    return_times: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for return flights using departure token."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY not found in environment variables")
        
    params = {
        "engine": "google_flights",
        "departure_id": departure_id.upper(),
        "arrival_id": arrival_id.upper(),
        "outbound_date": outbound_date,
        "return_date": return_date,
        "hl": "en",
        "adults": adults,
        "travel_class": travel_class,
        "include_airlines": SKYTEAM_AIRLINES,
        "api_key": api_key,
        "type": "1",
        "departure_token": departure_token
    }
    
    if return_times:
        params["outbound_times"] = return_times

    print(f"Debug: Return search params: {params}")
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        print(f"Debug: Raw API response: {results}")
        
        return_flights = results.get("return_flights", [])
        print(f"Debug: Return flights found: {len(return_flights)}")
        
        return return_flights[:MAX_FLIGHTS_TO_RETURN]
    except Exception as e:
        print(f"Debug: Return search failed with error: {str(e)}")
        raise RuntimeError(f"Return flight search failed: {str(e)}") from e

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
) -> FlightResult:
    """Wrapper function to handle both one-way and round-trip searches."""
    print(f"Debug: Starting search_flights with trip_type: {trip_type}")
    
    if trip_type == 1 and not return_date:
        raise ValueError("Return date is required for round trip flights")

    # Get outbound flights
    outbound_flights = search_outbound_flights(
        departure_id=departure_id,
        arrival_id=arrival_id,
        outbound_date=outbound_date,
        return_date=return_date if trip_type == 1 else None,
        adults=adults,
        travel_class=travel_class,
        outbound_times=outbound_times
    )
    
    print(f"Debug: Found {len(outbound_flights)} outbound flights")

    # For one-way flights, return the list directly
    if trip_type == 2:
        return outbound_flights

    # For round trips, get return flights for each outbound option
    round_trip_options: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    
    for outbound in outbound_flights:
        if "departure_token" not in outbound:
            print(f"Debug: No departure_token in outbound flight")
            continue
            
        try:
            return_flights = search_return_flights(
                departure_id=departure_id,
                arrival_id=arrival_id,
                outbound_date=outbound_date,
                return_date=return_date,
                departure_token=outbound["departure_token"],
                adults=adults,
                travel_class=travel_class,
                return_times=return_times
            )
            
            print(f"Debug: Found {len(return_flights)} return flights")
            
            # Pair each outbound flight with its first available return flight
            if return_flights:
                round_trip_options.append((outbound, return_flights[0]))
                
            if len(round_trip_options) >= MAX_FLIGHTS_TO_RETURN:
                break
                
        except Exception as e:
            print(f"Debug: Return flight search failed: {str(e)}")
            continue

    print(f"Debug: Returning {len(round_trip_options)} round trip options")
    return round_trip_options
