# mpr_loader.py
# P2.1: MPR Excel Loader with Column Validation
# Loads, validates, and caches MPR data for UC verification

from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

from config import normalize_state_name

# =============================================================================
# CONFIG: Expected MPR Columns (based on README)
# =============================================================================
# Identifier columns (used for project matching)
MPR_IDENTIFIER_COLS = [
    "State",
    "Component Name",
    "RUSA Phase",
    "Institution Name",
    "PAB Meeting Number",
    "PAB Date",  # Optional but recommended
]

# Amount columns (MPR side - for validation against UC)
MPR_AMOUNT_COLS = [
    # Approved
    "Total Amount Approved",
    "Central Share Approved",
    "State Share Approved",
    # Released
    "Total Amount Released",
    "Central Share Released",
    "State Share Released",
    # Utilised
    "Total Amount Utilised",
    "Central Share Utilised",
    "State Share Utilised",
]

# All required columns
REQUIRED_MPR_COLS = MPR_IDENTIFIER_COLS + MPR_AMOUNT_COLS

# =============================================================================
# Helper Functions
# =============================================================================


def normalize_column_name(col: str) -> str:
    """Normalize column names: strip, lower, replace spaces/dashes with underscores"""
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def validate_mpr_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate DataFrame has all required columns (case-insensitive)"""
    df_cols_normalized = {normalize_column_name(c): c for c in df.columns}
    missing = [
        req
        for req in REQUIRED_MPR_COLS
        if normalize_column_name(req) not in df_cols_normalized
    ]
    return (len(missing) == 0), missing


def _process_mpr_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Internal: Normalize columns + convert amounts to Decimal"""
    # Normalize column names
    col_mapping = {col: normalize_column_name(col) for col in df.columns}
    df = df.rename(columns=col_mapping)

    # 2. Normalize State Names into a new column 'state_canonical'
    # Determine source column
    source_col = "state_ut" if "state_ut" in df.columns else "state"
    if source_col in df.columns:
        df["state_canonical"] = df[source_col].apply(normalize_state_name)

    # Convert amount columns to Decimal (zero float drift)
    amount_cols = [normalize_column_name(c) for c in MPR_AMOUNT_COLS]
    for col in amount_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(str)
            df[col] = df[col].apply(
                lambda x: Decimal(x.strip()) if x.strip() else Decimal(0)
            )

    return df


# =============================================================================
# Main Loader: Fixed Path + Cache
# =============================================================================

MPR_FILE_PATH = Path("data/RUSA_MPR_March.xlsx")  # Relative to app root


@st.cache_data(ttl=86400)  # Cache 24 hours (or until app restart)
def load_mpr_data() -> Optional[pd.DataFrame]:
    """
    Load MPR from fixed path: data/RUSA_MPR_March.xlsx
    Returns validated DataFrame or None if failed.
    Cached to avoid re-reading on every session.
    """
    try:
        if not MPR_FILE_PATH.exists():
            st.error(f"⚠️ MPR file not found at: {MPR_FILE_PATH}")
            st.info(
                "💡 Please ensure 'data/RUSA_MPR_March.xlsx' exists in the app root directory."
            )
            return None

        df = pd.read_excel(MPR_FILE_PATH, engine="openpyxl")

        if df.empty:
            st.error("⚠️ MPR file is empty.")
            return None

        is_valid, missing_cols = validate_mpr_columns(df)
        if not is_valid:
            st.error(f"⚠️ MPR file missing required columns: {', '.join(missing_cols)}")
            st.info("💡 Expected columns (case-insensitive):")
            st.code(", ".join(REQUIRED_MPR_COLS), language="text")
            return None

        return _process_mpr_dataframe(df)

    except Exception as e:
        st.error(f"⚠️ Failed to load MPR: {str(e)}")
        return None
