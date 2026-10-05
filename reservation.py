"""
Parwaaz (پرواز) - Airline Reservation System

This file contains the reservation logic only.
There is no Streamlit code here.

The app.py file will use these Customer and Staff classes.
"""

# -----------------------------
# Flight settings
# -----------------------------

TOTAL_SEATS = 30

# Seat numbers:
# 1A 1B 1C | 1D 1E 1F
# 2A 2B 2C | 2D 2E 2F
# ...
# 5A 5B 5C | 5D 5E 5F

SEAT_LETTERS = ["A", "B", "C", "D", "E", "F"]

# Seat prices in PKR
ECONOMY_PRICE = 38000
BUSINESS_PRICE = 95000


# -----------------------------
# Helper functions
# -----------------------------

def get_seat_label(seat_number):
    """
    Convert a seat number into a label.

    Example:
        1 -> 1A
        2 -> 1B
        6 -> 1F
        7 -> 2A
        30 -> 5F
    """

    if not isinstance(seat_number, int):
        return None

    if seat_number < 1 or seat_number > TOTAL_SEATS:
        return None

    row = (seat_number - 1) // 6 + 1
    letter_index = (seat_number - 1) % 6

    return f"{row}{SEAT_LETTERS[letter_index]}"


def get_seat_class(seat_number):
    """
    Rows 1-2 = Business
    Rows 3-5 = Economy
    """

    if not isinstance(seat_number, int):
        return None

    if seat_number < 1 or seat_number > TOTAL_SEATS:
        return None

    row = (seat_number - 1) // 6 + 1

    if row <= 2:
        return "Business"

    return "Economy"


def get_seat_price(seat_number):
    """
    Return the price of a seat in PKR.
    """

    seat_class = get_seat_class(seat_number)

    if seat_class == "Business":
        return BUSINESS_PRICE

    if seat_class == "Economy":
        return ECONOMY_PRICE

    return None


def validate_seat(seat_number):
    """
    Check whether a seat number is valid.
    """

    return (
        isinstance(seat_number, int)
        and 1 <= seat_number <= TOTAL_SEATS
    )


# -----------------------------
# Customer class
# -----------------------------

class Customer:
    """
    Handles actions that a normal customer can perform.

    The class works with the two main lists:

    passenger_names
    seat_status
    """

    def __init__(self, passenger_names, seat_status):
        self.passenger_names = passenger_names
        self.seat_status = seat_status

    def view_available_seats(self):
        """
        Return a list of available seats.

        Example:
        [
            {"number": 1, "label": "1A", "class": "Business"},
            {"number": 2, "label": "1B", "class": "Business"}
        ]
        """

        available_seats = []

        for index in range(TOTAL_SEATS):
            if self.seat_status[index] == "Available":
                seat_number = index + 1

                available_seats.append(
                    {
                        "number": seat_number,
                        "label": get_seat_label(seat_number),
                        "class": get_seat_class(seat_number),
                        "price": get_seat_price(seat_number),
                    }
                )

        return available_seats

    def book_seat(self, name, seat):
        """
        Book one seat for a customer.

        Rules:
        - Name cannot be empty.
        - Seat must exist.
        - Seat cannot already be booked.
        - Customer cannot have more than 3 seats.
        """

        # Check name
        if not isinstance(name, str) or not name.strip():
            return {
                "success": False,
                "message": "Please enter a valid passenger name."
            }

        name = name.strip()

        # Check seat
        if not validate_seat(seat):
            return {
                "success": False,
                "message": "Invalid seat number. Please choose a seat from 1 to 30."
            }

        index = seat - 1

        # Check whether seat is already booked
        if self.seat_status[index] == "Booked":
            return {
                "success": False,
                "message": f"Seat {get_seat_label(seat)} is already booked."
            }

        # Count seats already booked by this customer
        customer_seat_count = 0

        for passenger in self.passenger_names:
            if passenger.strip().lower() == name.lower():
                customer_seat_count += 1

        if customer_seat_count >= 3:
            return {
                "success": False,
                "message": "A customer can book a maximum of 3 seats."
            }

        # Book the seat
        self.passenger_names[index] = name
        self.seat_status[index] = "Booked"

        return {
            "success": True,
            "message": f"Seat {get_seat_label(seat)} booked successfully.",
            "name": name,
            "seat": seat,
            "label": get_seat_label(seat),
            "class": get_seat_class(seat),
            "price": get_seat_price(seat),
        }

    def cancel_seat(self, name, seat):
        """
        Cancel a customer's booking.

        The passenger name must match the name
        currently assigned to the seat.
        """

        if not isinstance(name, str) or not name.strip():
            return {
                "success": False,
                "message": "Please enter the passenger name."
            }

        name = name.strip()

        if not validate_seat(seat):
            return {
                "success": False,
                "message": "Invalid seat number."
            }

        index = seat - 1

        # Check whether the seat is empty
        if self.seat_status[index] == "Available":
            return {
                "success": False,
                "message": f"Seat {get_seat_label(seat)} is already available."
            }

        # Check passenger name
        stored_name = self.passenger_names[index]

        if stored_name.strip().lower() != name.lower():
            return {
                "success": False,
                "message": "Passenger name does not match this booking."
            }

        # Cancel booking
        self.passenger_names[index] = "Empty"
        self.seat_status[index] = "Available"

        return {
            "success": True,
            "message": f"Booking for seat {get_seat_label(seat)} has been cancelled.",
            "seat": seat,
            "label": get_seat_label(seat),
        }

    def view_booking(self, name):
        """
        Find all bookings belonging to a passenger.
        """

        if not isinstance(name, str) or not name.strip():
            return {
                "success": False,
                "message": "Please enter a passenger name.",
                "bookings": []
            }

        name = name.strip()

        bookings = []

        for index in range(TOTAL_SEATS):
            if self.passenger_names[index].strip().lower() == name.lower():

                seat_number = index + 1

                bookings.append(
                    {
                        "seat": seat_number,
                        "label": get_seat_label(seat_number),
                        "class": get_seat_class(seat_number),
                        "price": get_seat_price(seat_number),
                        "name": self.passenger_names[index],
                    }
                )

        if not bookings:
            return {
                "success": False,
                "message": f"No booking found for {name}.",
                "bookings": []
            }

        return {
            "success": True,
            "message": f"Booking found for {name}.",
            "bookings": bookings,
        }


# -----------------------------
# Staff class
# -----------------------------

class Staff:
    """
    Handles staff/admin operations.
    """

    def __init__(self, passenger_names, seat_status):
        self.passenger_names = passenger_names
        self.seat_status = seat_status

    def view_all_seats(self):
        """
        Return information about all 30 seats.
        """

        seats = []

        for index in range(TOTAL_SEATS):
            seat_number = index + 1

            seats.append(
                {
                    "number": seat_number,
                    "label": get_seat_label(seat_number),
                    "class": get_seat_class(seat_number),
                    "price": get_seat_price(seat_number),
                    "status": self.seat_status[index],
                    "passenger": self.passenger_names[index],
                }
            )

        return seats

    def view_booked_passengers(self):
        """
        Return all currently booked passengers.
        """

        passengers = []

        for index in range(TOTAL_SEATS):
            if self.seat_status[index] == "Booked":

                seat_number = index + 1

                passengers.append(
                    {
                        "seat": seat_number,
                        "seat_label": get_seat_label(seat_number),
                        "passenger": self.passenger_names[index],
                        "class": get_seat_class(seat_number),
                        "price": get_seat_price(seat_number),
                    }
                )

        return passengers

    def search_passenger(self, name):
        """
        Search for a passenger by name.
        """

        if not isinstance(name, str) or not name.strip():
            return []

        name = name.strip().lower()

        results = []

        for index in range(TOTAL_SEATS):
            passenger = self.passenger_names[index]

            if passenger != "Empty" and name in passenger.lower():

                seat_number = index + 1

                results.append(
                    {
                        "seat": seat_number,
                        "seat_label": get_seat_label(seat_number),
                        "passenger": passenger,
                        "class": get_seat_class(seat_number),
                        "price": get_seat_price(seat_number),
                    }
                )

        return results

    def check_seat(self, seat):
        """
        Check one specific seat.
        """

        if not validate_seat(seat):
            return {
                "success": False,
                "message": "Invalid seat number."
            }

        index = seat - 1

        return {
            "success": True,
            "seat": seat,
            "label": get_seat_label(seat),
            "status": self.seat_status[index],
            "passenger": self.passenger_names[index],
            "class": get_seat_class(seat),
            "price": get_seat_price(seat),
        }

    def count_available_seats(self):
        """
        Count the number of available seats.
        """

        return self.seat_status.count("Available")

    def reset_flight(self):
        """
        Reset every seat to Available and every passenger to Empty.
        """

        for index in range(TOTAL_SEATS):
            self.passenger_names[index] = "Empty"
            self.seat_status[index] = "Available"

        return {
            "success": True,
            "message": "Flight has been reset successfully."
        }


# -----------------------------
# Sample booking data
# -----------------------------

def load_sample_bookings(passenger_names, seat_status):
    """
    Add sample Pakistani passengers so the application
    looks populated when it first opens.

    This function only fills empty seats.
    """

    sample_bookings = [
        ("Ahmad Khan", 3),
        ("Sara Ali", 7),
        ("Bilal Ahmed", 10),
        ("Fatima Noor", 14),
        ("Hassan Raza", 18),
        ("Ayesha Malik", 21),
        ("Usman Tariq", 25),
        ("Maham Shah", 28),
    ]

    for name, seat in sample_bookings:

        index = seat - 1

        # Only add the sample booking if the seat is empty.
        if (
            0 <= index < TOTAL_SEATS
            and passenger_names[index] == "Empty"
            and seat_status[index] == "Available"
        ):
            passenger_names[index] = name
            seat_status[index] = "Booked"