import streamlit as st
from ai_utils import get_model_response, update_parameters
from models import FlightParams, AIResponse
from booking_function import search_outbound_flights, search_return_flights
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

def display_flight_cards(flights: Union[List[Dict[str, Any]], List[Tuple[Dict[str, Any], Dict[str, Any]]]], trip_type: int):
    """Display flight results in a card format."""
    
    if trip_type == 1:  # Round trip
        # Add a back button if viewing return flights
        if any(return_flight is not None for _, return_flight in flights):
            if st.button("← Back to Outbound Flights"):
                # Reset to show only outbound flights
                st.session_state.flights = [(flight, None) for flight, _ in flights]
                st.rerun()
        
        for outbound, return_flight in flights:
            with st.container():
                st.markdown("---")
                cols = st.columns([3, 2])
                
                with cols[0]:
                    # Outbound flight
                    st.markdown("### Outbound Flight")
                    for segment in outbound["flights"]:
                        st.markdown(f"""
                        🛫 **{segment["departure_airport"]["time"]}** from {segment["departure_airport"]["name"]} ({segment["departure_airport"]["id"]})  
                        🛬 **{segment["arrival_airport"]["time"]}** at {segment["arrival_airport"]["name"]} ({segment["arrival_airport"]["id"]})  
                        ✈️ {segment["airline"]} {segment["flight_number"]}  
                        ⏱️ **Duration:** {segment["duration"]} mins
                        """)
                    
                    # Only show return flight if it exists
                    if return_flight:
                        st.markdown("### Return Flight")
                        for segment in return_flight["flights"]:
                            st.markdown(f"""
                            🛫 **{segment["departure_airport"]["time"]}** from {segment["departure_airport"]["name"]} ({segment["departure_airport"]["id"]})  
                            🛬 **{segment["arrival_airport"]["time"]}** at {segment["arrival_airport"]["name"]} ({segment["arrival_airport"]["id"]})  
                            ✈️ {segment["airline"]} {segment["flight_number"]}  
                            ⏱️ **Duration:** {segment["duration"]} mins
                            """)
                
                with cols[1]:
                    if return_flight:
                        # Show combined price for round trip
                        total_price = outbound.get("price", 0) + return_flight.get("price", 0)
                        total_duration = outbound.get("duration", 0) + return_flight.get("duration", 0)
                        flight_id = f"{hash(str(outbound))}{hash(str(return_flight))}"
                        button_text = "Select Round Trip"
                    else:
                        # Show just outbound price
                        total_price = outbound.get("price", 0)
                        total_duration = outbound.get("duration", 0)
                        flight_id = str(hash(str(outbound)))
                        button_text = "Select Outbound Flight"
                    
                    st.markdown(f"### ${total_price}")
                    st.markdown(f"*{outbound['flights'][0].get('travel_class', 'Economy')}*")
                    st.markdown(f"**Total Duration:** {total_duration} mins")
                    
                    if st.button(button_text, key=f"select_{flight_id}", type="primary"):
                        if return_flight:
                            # Final selection of round trip
                            st.session_state.selected_flight = (outbound, return_flight)
                            st.success("Round-trip flight selected!")
                        else:
                            # Search for return flights when outbound is selected
                            params = st.session_state.flight_params
                            with st.spinner("Searching for return flights..."):
                                try:
                                    return_flights = search_return_flights(
                                        departure_id=params.departure_id,  # Swap departure/arrival for return
                                        arrival_id=params.arrival_id,
                                        outbound_date=params.outbound_date,
                                        return_date=params.return_date,
                                        departure_token=outbound["departure_token"],
                                        adults=params.adults,
                                        travel_class=params.travel_class,
                                        return_times=params.return_times
                                    )
                                    print(return_flights)
                                    if return_flights:
                                        # Store the selected outbound flight with all possible returns
                                        st.session_state.flights = [
                                            (outbound, return_flight) 
                                            for return_flight in return_flights
                                        ]
                                        st.rerun()
                                    else:
                                        st.error("No return flights found for the selected outbound flight.")
                                except Exception as e:
                                    st.error(f"Error searching for return flights: {str(e)}")
    
    else:  # One way
        for flight in flights:
            with st.container():
                st.markdown("---")
                cols = st.columns([3, 2])
                
                with cols[0]:
                    for segment in flight["flights"]:
                        st.markdown(f"""
                        🛫 **{segment["departure_airport"]["time"]}** from {segment["departure_airport"]["name"]} ({segment["departure_airport"]["id"]})  
                        🛬 **{segment["arrival_airport"]["time"]}** at {segment["arrival_airport"]["name"]} ({segment["arrival_airport"]["id"]})  
                        ✈️ {segment["airline"]} {segment["flight_number"]}  
                        ⏱️ **Duration:** {segment["duration"]} mins
                        """)
                
                with cols[1]:
                    st.markdown(f"### ${flight.get('price', 'Unknown')}")
                    st.markdown(f"*{flight['flights'][0].get('travel_class', 'Economy')}*")
                    st.markdown(f"**Total Duration:** {flight.get('duration', 'Unknown')} mins")
                    
                    flight_id = str(hash(str(flight)))
                    if st.button("Select Flight", key=f"select_{flight_id}", type="primary"):
                        st.session_state.selected_flight = flight
                        st.success("Flight selected!")

def main():
    st.title("Tailwind")

    # Initialize states
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "flight_params" not in st.session_state:
        st.session_state.flight_params = FlightParams()
    if "search_mode" not in st.session_state:
        st.session_state.search_mode = False

    # Chat interface (only show if not in search mode)
    if not st.session_state.search_mode:
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("How can I help you book a flight today?"):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            ai_response = get_model_response(prompt, st.session_state.flight_params)
            
            # Only update parameters if we got a valid response
            if ai_response:
                updated_params = update_parameters(st.session_state.flight_params, ai_response)
                st.session_state.flight_params = updated_params
                
                with st.chat_message("assistant"):
                    if ai_response.message:
                        st.markdown(ai_response.message)
                    params_display = st.session_state.flight_params.dict(exclude_none=True)
                    if params_display:
                        st.json(params_display)

                if ai_response.message:
                    st.session_state.messages.append({"role": "assistant", "content": ai_response.message})

        # Show search button when parameters are complete
        if st.session_state.flight_params.completion:
            st.success("All parameters collected. Ready to search for flights!")
            if st.button("Search Flights"):
                st.session_state.search_mode = True
                with st.spinner("Searching for available flights..."):
                    try:
                        params = st.session_state.flight_params
                        
                        # For both one-way and round-trip, we need to search outbound
                        outbound_flights = search_outbound_flights(
                            departure_id=params.departure_id,
                            arrival_id=params.arrival_id,
                            outbound_date=params.outbound_date,
                            return_date=params.return_date or params.outbound_date,  # Use outbound_date as return_date for one-way
                            adults=params.adults,
                            travel_class=params.travel_class,
                            outbound_times=params.outbound_times
                        )
                        
                        if outbound_flights:
                            if params.trip_type == 1:  # Round trip
                                # Store outbound flights without return flights
                                st.session_state.flights = [(flight, None) for flight in outbound_flights if "departure_token" in flight]
                            else:  # One way
                                st.session_state.flights = outbound_flights
                            st.rerun()
                        else:
                            st.error("No flights found matching your criteria.")
                            st.session_state.search_mode = False
                            
                    except Exception as e:
                        st.error(f"Error searching for flights: {str(e)}")
                        st.session_state.search_mode = False

    # Search results mode
    else:
        if "flights" in st.session_state and st.session_state.flights:
            st.subheader("Available Flights")
            display_flight_cards(
                st.session_state.flights, 
                st.session_state.flight_params.trip_type
            )
            

if __name__ == "__main__":
    main() 