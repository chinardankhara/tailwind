from ai_utils import run_booking_loop
from booking_function import search_flights
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    try:
        # Start the booking loop
        initial_prompt = "I want to book a flight."
        flight_params = run_booking_loop(initial_prompt)

        if flight_params.completion:
            # Search for flights using the collected parameters
            try:
                flights = search_flights(
                    departure_id=flight_params.departure_id,
                    arrival_id=flight_params.arrival_id,
                    outbound_date=flight_params.outbound_date,
                    trip_type=flight_params.trip_type,
                    return_date=flight_params.return_date,
                    adults=flight_params.adults,
                    travel_class=flight_params.travel_class,
                    api_key=os.getenv("SERPAPI_API_KEY"),
                )
                print(f"\nTop {len(flights)} Flights Found:")
                for idx, flight in enumerate(flights, start=1):
                    print(f"\nFlight {idx}:")
                    for key, value in flight.items():
                        print(f"  {key}: {value}")
            except Exception as e:
                print(f"Error searching flights: {str(e)}")
        else:
            print("Booking process was not completed.")

    except Exception as e:
        print(f"Error during booking process: {str(e)}")

if __name__ == "__main__":
    main() 