# config.py
# Hardcoded configuration for UC Verification Portal (P1)

# Central Share : State Share Ratios per State/UT & Component
# Format: { "State/UT": { "Component": (central_ratio, state_ratio), ... } }
CS_SS_RATIOS = {
    "Andhra Pradesh": {
        "MMER": (100, 0),
        "Other": (60, 40),
    },
    "Arunchal Pradesh": {
        "Other": (90, 10),
        "MMER": (100, 0),
        "EMDC": (50, 50),
    },
    "Assam": {
        "Other": (90, 10),
        "MMER": (100, 0),
        "EMDC": (50, 50),
    },
    "Bihar": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Chhattisgarh": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Goa": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Gujarat": {
        "MMER": (100, 0),
        "Other": (60, 40),
        "EMDC": (33, 67),
    },
    "Haryana": {
        "Other": (60, 40),
    },
    "Jammu & Kashmir": {
        "Other": (90, 10),
        "MMER": (100, 0),
    },
    "Jharkhand": {
        "Other": (),
        "MMER": (100, 0),
        "EMDC": (),
    },
    "Karnataka": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Kerala": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Madhya Pradesh": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Maharashtra": {
        "Other": (60, 40),
        "MMER": (100, 0),
        "EMDC": (33, 67),
    },
    "Manipur": {
        "Other": (90, 10),
    },
    "Meghalaya": {
        "Other": (90, 10),
        "MMER": (100, 0),
    },
    "Mizoram": {
        "Other": (90, 10),
    },
    "Nagaland": {
        "Other": (90, 10),
        "MMER": (100, 0),
    },
    "Odisha": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Puducherry": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Punjab": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Rajasthan": {
        "Other": (),
        "MMER": (100, 0),
    },
    "Sikkim": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Tamil Nadu": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Telangana": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Tripura": {
        "Other": (90, 10),
        "MMER": (100, 0),
    },
    "Uttar Pradesh": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Uttarakhand": {
        "Other": (90, 10),
        "MMER": (100, 0),
    },
    "West Bengal": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
}

# Hardcoded User Credentials (Username -> Password -> Role)
# Note: For a 15-30 day internal tool, this is secure enough.
USERS = {
    "admin1": {"password": "Admin@Secure1", "role": "Admin"},
    "admin2": {"password": "Admin@Secure2", "role": "Admin"},
    # Add 14 consultants here
    "consultant1": {"password": "Cons@123", "role": "Consultant"},
    "consultant2": {"password": "Cons@123", "role": "Consultant"},
    # ...
}

# Available States/UTs & Components (derived from ratios config)
STATES_UTS = list(CS_SS_RATIOS.keys())

# Scheme constants (matches README)
SCHEMES = ["RUSA 1", "RUSA 2", "PM-USHA"]


# Helper: Resolve ratio with fallback logic
def get_ratio(state: str, component: str) -> tuple[int, int]:
    """
    Returns (central_ratio, state_ratio) for given state+component.
    Fallback order: exact component → "Other" → default (60,40)
    """
    try:
        state_ratios = CS_SS_RATIOS.get(state, {})
        return state_ratios.get(component, state_ratios.get("Other", (60, 40)))
    except Exception:
        # Graceful fallback if config is malformed
        return (60, 40)
