# template_generator.py
# P2.2: UC Template Generator
# Generates pre-populated UC Excel template for a given State/UT

import pandas as pd
import io
from typing import Optional
from decimal import Decimal

# =============================================================================
# CONFIG: UC Template Columns (per README)
# =============================================================================

# Pre-populated fields (copied from MPR)
# Mapping: UC Display Name -> MPR Normalized Column Name
UC_PREFILLED_COLS = {
    "State/UT": "state_ut",
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
def generate_uc_template_bytes(
    filtered_mpr_df: pd.DataFrame,
    selected_state: str
) -> Optional[bytes]:
    """
    Generate UC template from a PRE-FILTERED DataFrame.
    """
    if filtered_mpr_df is None or filtered_mpr_df.empty:
        return None

    # Build prefilled section
    prefilled = pd.DataFrame()
    for uc_col, mpr_col in UC_PREFILLED_COLS.items():
        if mpr_col in filtered_mpr_df.columns:
            if mpr_col in [
                "total_amount_approved",
                "central_share_approved",
                "state_share_approved",
            ]:
                prefilled[uc_col] = filtered_mpr_df[mpr_col].apply(
                    lambda x: str(x) if isinstance(x, Decimal) else str(x)
                )
            else:
                prefilled[uc_col] = filtered_mpr_df[mpr_col]
        else:
            prefilled[uc_col] = ""

    # Add blank UC columns
    for col in UC_BLANK_COLS:
        prefilled[col] = ""

    # Reorder
    template_df = prefilled[UC_TEMPLATE_COLUMNS]

    # Write to Excel
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            template_df.to_excel(writer, sheet_name="UC_Template", index=False)
            worksheet = writer.sheets["UC_Template"]

            # Auto-adjust widths
            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        if cell.value is not None and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except ValueError:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    except Exception as e:
        print(f"Error generating Excel: {e}")
        return None

    output.seek(0)
    return output.getvalue()
