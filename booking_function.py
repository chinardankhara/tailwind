from typing import List, Dict, Any, Optional, Tuple, Union
from serpapi import GoogleSearch
from datetime import datetime
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Configuration constants
MAX_FLIGHTS_TO_RETURN = 5
SKYTEAM_AIRLINES = "SKYTEAM"

FlightResult = Union[List[Dict[str, Any]], List[Tuple[Dict[str, Any], Dict[str, Any]]]]

# Add caching for outbound flights search
@st.cache_data(ttl=3600)  # Cache for 1 hour
def search_outbound_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,  # Required for SerpAPI
    adults: int = 1,
    travel_class: int = 1,
    outbound_times: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for outbound flights with caching."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY not found in environment variables")
        
    params = {
        "engine": "google_flights",
        "departure_id": departure_id.upper(),
        "arrival_id": arrival_id.upper(),
        "outbound_date": outbound_date,
        "return_date": return_date,  # Always required
        "hl": "en",
        "adults": adults,
        "travel_class": travel_class,
        "include_airlines": SKYTEAM_AIRLINES,
        "api_key": api_key,
        "type": "1"
    }
    
    if outbound_times:
        params["outbound_times"] = outbound_times

    print(f"Debug: Outbound search params: {params}")
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        best_flights = results.get("best_flights", [])
        return best_flights[:MAX_FLIGHTS_TO_RETURN]
    except Exception as e:
        print(f"Debug: Search failed with error: {str(e)}")
        raise RuntimeError(f"Outbound flight search failed: {str(e)}") from e

# Add caching for return flights search
@st.cache_data(ttl=3600)  # Cache for 1 hour
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
    """Search for return flights with caching."""
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
        return_flights = results.get("best_flights", [])
        return return_flights[:MAX_FLIGHTS_TO_RETURN]
    except Exception as e:
        print(f"Debug: Return search failed with error: {str(e)}")
        raise RuntimeError(f"Return flight search failed: {str(e)}") from e

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_booking_url(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str],
    trip_type: int,
    booking_token: str,
) -> str:
    """Get the Google Flights booking URL for the selected flight."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY not found in environment variables")
        
    params = {
        "engine": "google_flights",
        "booking_token": booking_token,
        "departure_id": departure_id.upper(),
        "arrival_id": arrival_id.upper(),
        "outbound_date": outbound_date,
        "hl": "en",
        "api_key": api_key,
        "type": 2 if trip_type == 2 else 1  # Explicitly set type for one-way flights
    }
    
    # For round trips or SerpAPI requirements
    if trip_type == 1:
        params["return_date"] = return_date 
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        booking_url = results["search_metadata"]["google_flights_url"]
        return booking_url
    except Exception as e:
        print(f"Debug: Booking URL retrieval failed with error: {str(e)}")
        raise RuntimeError(f"Failed to get booking URL: {str(e)}") from e
