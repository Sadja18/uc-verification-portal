# template_generator.py
# P2.2: UC Template Generator
# Generates pre-populated UC Excel template for a given State

import pandas as pd
import io
from typing import Optional
from decimal import Decimal

# =============================================================================
# CONFIG: UC Template Columns (per README)
# =============================================================================

# Pre-populated fields (copied from MPR)
UC_PREFILLED_COLS = {
    # Display Name in Excel → MPR normalized column name
    "State": "state_ut",
    "Component Name": "component_name",
    "RUSA Phase": "rusa_phase",
    "District": "district",
    "Institution Name": "institution_name",
    "PAB Date": "pab_date",
    "PAB Meeting Number": "pab_meeting_number",
    "Total Amount Approved": "total_amount_approved",
    "Central Share Approved": "central_share_approved",
    "State Share Approved": "state_share_approved",
}

# Blank fields for user to fill (UC-side amounts)
UC_BLANK_COLS = [
    "Total Amount Approved (UC)",
    "Central Share Amount Approved (UC)",
    "State Share Amount Approved (UC)",
    "Total Amount Released (UC)",
    "Central Share Amount Released (UC)",
    "State Share Amount Released (UC)",
    "Total Amount Utilised (UC)",
    "Central Share Amount Utilised (UC)",
    "State Share Amount Utilised (UC)",
]

# Final column order for UC template (prefilled first, then blanks)
UC_TEMPLATE_COLUMNS = list(UC_PREFILLED_COLS.keys()) + UC_BLANK_COLS

# =============================================================================
# Core Generator Function
# =============================================================================


def generate_uc_template_bytes(mpr_df: pd.DataFrame, state: str) -> Optional[bytes]:
    """
    Generate UC template Excel (as bytes) for given State.

    Steps:
    1. Filter MPR for selected state (case-insensitive)
    2. Select & rename prefilled columns to UC template names
    3. Add blank UC amount columns
    4. Format amounts as strings (preserve Decimal precision)
    5. Return Excel file bytes for download
    """
    
    print(mpr_df.head(1).to_dict(orient='records'))
    print(mpr_df.columns)
    if mpr_df is None or "state" not in mpr_df.columns:
        return None

    # Filter projects for selected state
    state_projects = mpr_df[mpr_df["state"].str.lower() == state.lower()].copy()

    if state_projects.empty:
        return None

    # Build prefilled section: rename MPR columns → UC template display names
    prefilled = pd.DataFrame()
    for uc_col, mpr_col in UC_PREFILLED_COLS.items():
        if mpr_col in state_projects.columns:
            # Convert Decimal amounts to string for Excel (no float drift)
            if mpr_col in [
                "total_amount_approved",
                "central_share_approved",
                "state_share_approved",
            ]:
                prefilled[uc_col] = state_projects[mpr_col].apply(
                    lambda x: str(x) if isinstance(x, Decimal) else str(x)
                )
            else:
                prefilled[uc_col] = state_projects[mpr_col]
        else:
            # Fallback: add column with empty string if MPR missing it
            prefilled[uc_col] = ""

    # Add blank UC amount columns (empty strings for user to fill)
    for col in UC_BLANK_COLS:
        prefilled[col] = ""

    # Reorder columns exactly as per spec
    template_df = prefilled[UC_TEMPLATE_COLUMNS]

    # Write to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template_df.to_excel(writer, sheet_name="UC_Template", index=False)

        # Optional: Format amount columns for better UX (text format to preserve precision)
        workbook = writer.book
        worksheet = writer.sheets["UC_Template"]
        text_format = workbook.add_format({"num_format": "@"})  # Text format

        # Apply text format to all amount columns (both prefilled and blank)
        amount_cols = [c for c in UC_TEMPLATE_COLUMNS if "Amount" in c or "Share" in c]
        for col_idx, col_name in enumerate(UC_TEMPLATE_COLUMNS):
            if col_name in amount_cols:
                # Set column width + text format
                worksheet.set_column(col_idx, col_idx, 20, text_format)

    output.seek(0)
    return output.getvalue()
