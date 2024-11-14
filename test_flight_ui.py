import streamlit as st
from datetime import datetime, timedelta

def generate_dummy_flights() -> list:
    """Generate dummy flight data for testing."""
    base_time = datetime.now()
    
    return [
        {
            "id": "F1",
            "price": 450,
            "departure_time": (base_time + timedelta(hours=2)).strftime("%I:%M %p"),
            "arrival_time": (base_time + timedelta(hours=5)).strftime("%I:%M %p"),
            "departure_airport": "ATL",
            "arrival_airport": "CDG",
            "duration": "7h 30m",
            "airline": "Delta",
            "cabin_class": "Economy",
            "layovers": []
        },
        {
            "id": "F2",
            "price": 850,
            "departure_time": (base_time + timedelta(hours=4)).strftime("%I:%M %p"),
            "arrival_time": (base_time + timedelta(hours=8)).strftime("%I:%M %p"),
            "departure_airport": "ATL",
            "arrival_airport": "CDG",
            "duration": "7h 45m",
            "airline": "Air France",
            "cabin_class": "Premium Economy",
            "layovers": [
                {
                    "airport": "JFK",
                    "duration": "1h 30m"
                }
            ]
        },
        {
            "id": "F3",
            "price": 1250,
            "departure_time": (base_time + timedelta(hours=6)).strftime("%I:%M %p"),
            "arrival_time": (base_time + timedelta(hours=10)).strftime("%I:%M %p"),
            "departure_airport": "ATL",
            "arrival_airport": "CDG",
            "duration": "8h 15m",
            "airline": "Delta",
            "cabin_class": "Business",
            "layovers": []
        }
    ]

def display_flight_results(flights: list):
    """Display flight search results in a user-friendly format."""
    
    if not flights:
        st.warning("No flights found matching your criteria.")
        return

    # Add filters in the sidebar
    with st.sidebar:
        st.subheader("Filter Results")
        max_price = st.slider(
            "Maximum Price", 
            min_value=min(f["price"] for f in flights),
            max_value=max(f["price"] for f in flights),
            value=max(f["price"] for f in flights)
        )
        nonstop_only = st.checkbox("Non-stop flights only")
        preferred_airline = st.multiselect(
            "Preferred Airlines", 
            options=list(set(f["airline"] for f in flights))
        )

    # Filter flights based on user preferences
    filtered_flights = [
        f for f in flights 
        if f["price"] <= max_price
        and (not nonstop_only or not f["layovers"])
        and (not preferred_airline or f["airline"] in preferred_airline)
    ]

    if not filtered_flights:
        st.warning("No flights match your filters.")
        return

    st.subheader("🌟 Flight Options")
    
    for flight in filtered_flights:
        with st.expander(
            f"${flight['price']} - {flight['departure_time']} to {flight['arrival_time']}", 
            expanded=True
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Flight details
                st.markdown(f"""
                **Departure:** {flight['departure_time']} from {flight['departure_airport']}  
                **Arrival:** {flight['arrival_time']} at {flight['arrival_airport']}  
                **Duration:** {flight['duration']}  
                **Airline:** {flight['airline']}
                """)
                
                if flight.get("layovers"):
                    st.markdown("**Layovers:**")
                    for layover in flight["layovers"]:
                        st.markdown(f"- {layover['airport']} ({layover['duration']})")
            
            with col2:
                # Price and booking section
                st.markdown(f"### ${flight['price']}")
                st.markdown(f"*{flight['cabin_class']}*")
                if st.button("Select Flight", key=f"select_{flight['id']}", type="primary"):
                    st.session_state.selected_flight = flight
                    st.success("Flight selected! Ready to proceed to booking.")

def main():
    st.title("Flight Search Results UI Test")
    
    # Generate dummy data
    if "flights" not in st.session_state:
        st.session_state.flights = generate_dummy_flights()
    
    # Add a reset button
    if st.button("Reset Test Data"):
        st.session_state.flights = generate_dummy_flights()
        if "selected_flight" in st.session_state:
            del st.session_state.selected_flight
    
    # Display flights
    display_flight_results(st.session_state.flights)
    
    # Show selected flight details
    if "selected_flight" in st.session_state:
        st.divider()
        st.subheader("Selected Flight Details")
        st.json(st.session_state.selected_flight)

if __name__ == "__main__":
    main() 