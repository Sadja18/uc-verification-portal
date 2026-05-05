# config.py
# Hardcoded configuration for UC Verification Portal (P1)

# Central Share : State Share Ratios per State/UT & Component
# Format: { "State/UT": { "Component": (central_ratio, state_ratio), ... } }
CS_SS_RATIOS = {
    "Andaman and Nicobar Islands": {
        "Other": (100, 0),
        "MMER": (100, 0),
    },
    "Andhra Pradesh": {
        "MMER": (100, 0),
        "Other": (60, 40),
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
    "Chandigarh": {
        "Other": (100, 0),
        "MMER": (100, 0),
    },
    "Chhattisgarh": {
        "Other": (60, 40),
        "MMER": (100, 0),
    },
    "Delhi": {
        "Other": (100, 0),
        "MMER": (100, 0),
    },
    "Dadra and Nagar Haveli and Daman and Diu": {
        "Other": (100, 0),
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
    "Himachal Pradesh":{
        "Other":(60,40),
        "MMER": (100,0)
    },
    "Jammu and Kashmir": {
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
    "Ladakh": {
        "Other": (100, 0),
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

# Available States/UTs & Components (derived from ratios config)
STATES_UTS = list(CS_SS_RATIOS.keys())

# Scheme constants (matches README)
SCHEMES = ["RUSA 1", "RUSA 2", "PM-USHA"]


# Helper: Resolve ratio with fallback logic
def get_ratio(state: str, component: str) -> tuple[int, int]:
    """
    Returns (central_ratio, state_ratio) for given state+component.

    Logic:
    1. Uses Canonical State Name for lookup.
    2. Maps Component to one of three keys: 'MMER', 'EMDC', or 'Other'.
        - 'MMER' -> Exact match.
        - 'EMDC' -> Matches 'EMDC' or 'Erstwhile MDC'.
        - 'Other' -> Default for everything else.
    3. Fallback to (60, 40) if state/component not found in config.
    """
    try:
        # 1. Get ratios for the canonical state
        state_ratios = CS_SS_RATIOS.get(state, {})

        # 2. Determine the component category key
        comp_clean = str(component).strip()

        if comp_clean == "MMER":
            comp_key = "MMER"
        elif comp_clean in ["EMDC", "Erstwhile MDC"]:
            comp_key = "EMDC"
        else:
            comp_key = "Other"

        # 3. Lookup ratio: Specific Key -> Other -> Default (60, 40)
        ratio = state_ratios.get(comp_key, state_ratios.get("Other", (60, 40)))

        return ratio

    except Exception:
        # Graceful fallback if config is malformed
        return (60, 40)


STATE_VARIANTS = {
    "Andaman and Nicobar Islands": ["andaman and nicobar islands"],
    "Andhra Pradesh": ["andhra pradesh"],
    "Assam": ["assam"],
    "Bihar": ["bihar"],
    "Chandigarh": ["chandigarh"],
    "Chhattisgarh": ["chhattisgarh"],
    "Delhi": ["delhi", "nct of delhi"],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "dadra and nagar haveli and daman and diu",
        "the dadra and nagar haveli and daman and diu",
        "dadra & nagar haveli",
        "dadra and nagar haveli",
        "daman and diu",
        "dnhdd",
    ],
    "Goa": ["goa"],
    "Gujarat": ["gujarat"],
    "Haryana": ["haryana"],
    "Himachal Pradesh": ["himachal pradesh", 'himachal pradesh'],
    "Jammu and Kashmir": ["jammu and kashmir", "j&k", "j and k"],
    "Jharkhand": ["jharkhand"],
    "Karnataka": ["karnataka"],
    "Kerala": ["kerala"],
    "Ladakh": ["ladakh"],
    "Madhya Pradesh": ["madhya pradesh"],
    "Maharashtra": ["maharashtra"],
    "Manipur": ["manipur"],
    "Meghalaya": ["meghalaya"],
    "Mizoram": ["mizoram"],
    "Nagaland": ["nagaland"],
    "Odisha": ["odisha", "orissa"],
    "Puducherry": ["puducherry", "pondicherry"],
    "Punjab": ["punjab"],
    "Rajasthan": ["rajasthan"],
    "Sikkim": ["sikkim"],
    "Tamil Nadu": ["tamil nadu"],
    "Telangana": ["telangana"],
    "Tripura": ["tripura"],
    "Uttar Pradesh": ["uttar pradesh"],
    "Uttarakhand": ["uttarakhand"],
    "West Bengal": ["west bengal"],
}


# Helper: Get list of Canonical States for Dropdown
def get_canonical_states():
    return sorted(list(STATE_VARIANTS.keys()))


# Helper: Normalize a raw state name to Canonical
def normalize_state_name(raw_name: str) -> str:
    if not raw_name:
        return ""
    
    # Standardize the input: lowercase, strip, and swap & for 'and'
    clean_name = str(raw_name).strip().lower().replace("&", "and")

    for canonical, variants in STATE_VARIANTS.items():
        # Standardize variants the SAME way as the input
        standardized_variants = [v.lower().replace("&", "and").strip() for v in variants]
        
        if clean_name in standardized_variants:
            return canonical

    return str(raw_name).strip().title()


# Helper: Get list of raw variants for a canonical state (for filtering)
def get_state_variants(canonical_name: str) -> list[str]:
    return STATE_VARIANTS.get(canonical_name, [canonical_name.lower()])
