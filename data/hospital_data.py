"""Dummy hospital data for the demo. No database — plain constants, swapped for a real data source once this moves past the demo stage."""

HOSPITAL_NAME = "Saudia Specialist Hospital"

DOCTORS = [
    {
        "name": "Dr. Ahmed Al-Fahad",
        "specialty": "Cardiology",
        "available_days": ["Sunday", "Tuesday", "Thursday"],
        "available_times": "9:00 AM - 1:00 PM",
    },
    {
        "name": "Dr. Sara Khalid",
        "specialty": "Pediatrics",
        "available_days": ["Sunday", "Monday", "Wednesday"],
        "available_times": "10:00 AM - 4:00 PM",
    },
    {
        "name": "Dr. Yousef Al-Mansour",
        "specialty": "Dermatology",
        "available_days": ["Monday", "Wednesday", "Thursday"],
        "available_times": "1:00 PM - 6:00 PM",
    },
    {
        "name": "Dr. Fatima Al-Zahrani",
        "specialty": "Orthopedics",
        "available_days": ["Sunday", "Tuesday", "Wednesday"],
        "available_times": "9:00 AM - 2:00 PM",
    },
    {
        "name": "Dr. Omar Siddiqui",
        "specialty": "General Medicine",
        "available_days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
        "available_times": "8:00 AM - 8:00 PM",
    },
]

INSURANCE_PROVIDERS = [
    "Bupa Arabia",
    "Tawuniya",
    "MedGulf",
    "Al Rajhi Takaful",
]

HOSPITAL_HOURS = "Saturday to Thursday, 8:00 AM - 10:00 PM"

HOSPITAL_LOCATION = "King Fahd Road, Riyadh"
