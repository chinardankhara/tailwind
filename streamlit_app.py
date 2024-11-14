import streamlit as st
from ai_utils import get_model_response, update_parameters
from models import FlightParams, AIResponse
from booking_function import search_flights
from datetime import datetime

def display_flight_cards(flights: list):
    """Display flight results in a card format."""
    for flight in flights:
        with st.container():
            st.markdown("---")  # Divider between flights
            cols = st.columns([3, 2])
            
            with cols[0]:
                # Flight details for first leg of journey
                first_flight = flight["flights"][0]
                airline = first_flight.get("airline", "Unknown Airline")
                st.markdown(f"### {airline}")
                
                # Show all flight segments
                for segment in flight["flights"]:
                    st.markdown(f"""
                    🛫 **{segment["departure_airport"]["time"]}** from {segment["departure_airport"]["name"]} ({segment["departure_airport"]["id"]})  
                    🛬 **{segment["arrival_airport"]["time"]}** at {segment["arrival_airport"]["name"]} ({segment["arrival_airport"]["id"]})  
                    ⏱️ **Duration:** {segment.get("duration", "Unknown")} mins
                    """)
                
                # Show layovers if any
                if flight.get("layovers"):
                    st.markdown("**Layovers:**")
                    for layover in flight["layovers"]:
                        duration = layover.get("duration", "Unknown")
                        airport = layover.get("name", "Unknown Airport")
                        st.markdown(f"- {airport} ({duration} mins)")
            
            with cols[1]:
                # Price and booking
                price = flight.get("price", "Unknown")  # Price is directly in the flight
                st.markdown(f"### ${price}")
                
                # Get travel class from first flight segment
                travel_class = first_flight.get("travel_class", "Economy")
                st.markdown(f"*{travel_class}*")
                
                flight_id = flight.get('id', str(hash(str(flight))))  # Fallback to hash if no ID
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
                st.session_state.search_mode = True  # Enable search mode
                with st.spinner("Searching for available flights..."):
                    try:
                        params = st.session_state.flight_params
                        flights = search_flights(
                            departure_id=params.departure_id,
                            arrival_id=params.arrival_id,
                            outbound_date=params.outbound_date,
                            trip_type=params.trip_type,
                            return_date=params.return_date,
                            adults=params.adults,
                            travel_class=params.travel_class,
                            outbound_times=params.outbound_times,
                            return_times=params.return_times
                        )
                        st.session_state.flights = flights
                        st.rerun()  # Rerun to refresh the UI
                    except Exception as e:
                        st.error(f"Error searching for flights: {str(e)}")
                        st.session_state.search_mode = False

    # Search results mode
    else:
        if "flights" in st.session_state and st.session_state.flights:
            st.subheader("Available Flights")
            display_flight_cards(st.session_state.flights)
            
            # Add a button to start over
            if st.button("New Search"):
                st.session_state.search_mode = False
                st.session_state.messages = []
                st.session_state.flight_params = FlightParams()
                st.session_state.pop('flights', None)
                st.rerun()

if __name__ == "__main__":
    main() 