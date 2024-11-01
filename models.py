from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class FlightParams(BaseModel):
    departure_id: Optional[str] = Field(
        None, 
        description="Airport code for departure (e.g., 'CDG')",
        pattern="^[A-Z]{3}$"
    )
    arrival_id: Optional[str] = Field(
        None, 
        description="Airport code for arrival (e.g., 'AUS')",
        pattern="^[A-Z]{3}$"
    )
    trip_type: Optional[int] = Field(
        None, 
        description="1 for round trip, 2 for one way",
        ge=1,
        le=2
    )
    outbound_date: Optional[str] = Field(
        None, 
        description="Departure date in YYYY-MM-DD format",
        pattern="^\d{4}-\d{2}-\d{2}$"
    )
    return_date: Optional[str] = Field(
        None, 
        description="Return date in YYYY-MM-DD format (required if trip_type is 1)",
        pattern="^\d{4}-\d{2}-\d{2}$"
    )
    adults: int = Field(
        1, 
        ge=1,
        description="Number of adult passengers"
    )
    travel_class: int = Field(
        1,
        ge=1,
        le=4,
        description="1=Economy, 2=Premium Economy, 3=Business, 4=First"
    )
    completion: bool = Field(
        False,
        description="Indicates whether all required parameters are filled"
    )
    outbound_times: Optional[str] = Field(
        None,
        description="Comma-separated time ranges for outbound flight (e.g., '4,18,3,19')"
    )
    return_times: Optional[str] = Field(
        None,
        description="Comma-separated time ranges for return flight (e.g., '4,18,3,19')"
    )

    @validator("departure_id", "arrival_id")
    def airport_code_must_be_valid(cls, v):
        if v and not v.isalpha():
            raise ValueError("Airport codes must contain only letters.")
        return v.upper() if v else v

    @validator("outbound_date", "return_date")
    def date_must_be_valid(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format.")
        return v

    @validator("return_date")
    def return_date_required_for_round_trip(cls, v, values):
        if values.get("trip_type") == 1 and not v:
            raise ValueError("Return date is required for round trip flights.")
        if v and values.get("outbound_date"):
            outbound = datetime.strptime(values["outbound_date"], "%Y-%m-%d")
            return_dt = datetime.strptime(v, "%Y-%m-%d")
            if return_dt < outbound:
                raise ValueError("Return date cannot be before departure date.")
        return v

    @validator("outbound_times", "return_times")
    def validate_times(cls, v):
        if v is None:
            return v
        try:
            times = [int(t.strip()) for t in v.split(",")]
            if len(times) not in [2, 4]:
                raise ValueError("Times must contain either 2 or 4 comma-separated numbers")
            if any(t < 0 or t > 23 for t in times):
                raise ValueError("Times must be between 0 and 23")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid time format: {str(e)}")


class AIResponse(BaseModel):
    departure_id: Optional[str] = None
    arrival_id: Optional[str] = None
    trip_type: Optional[int] = None
    outbound_date: Optional[str] = None
    return_date: Optional[str] = None
    adults: Optional[int] = None
    travel_class: Optional[int] = None
    message: Optional[str] = None  # Message to prompt the user
    completion: Optional[bool] = False 
    outbound_times: Optional[str] = None
    return_times: Optional[str] = None