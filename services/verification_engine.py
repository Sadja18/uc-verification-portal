import logging
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

from config import get_ratio  # Dynamic ratio resolution[cite: 4]

logger = logging.getLogger("VerificationEngine")


class VerificationEngine:
    def __init__(self, master_df: pd.DataFrame):
        self.master_df = master_df
        # Display Mapping (UC Total headers remain for database parity)[cite: 3, 9]
        self.display_to_db = {
            "State": "state_canonical",
            "Phase": "rusa_phase",
            "Component": "component",
            "Institution Name": "inst_name",
            "MPR Total Appr.": "mpr_total_appr",
            "UC Total Appr.": "uc_total_appr",
            "UC Central Appr.": "uc_central_appr",
            "UC State Appr.": "uc_state_appr",
            "UC Total Released": "uc_total_rel",
            "UC Central Released": "uc_central_rel",
            "UC State Released": "uc_state_rel",
            "UC Total Utilized": "uc_total_util",
            "UC Central Utilized": "uc_central_util",
            "UC State Utilized": "uc_state_util",
            "project_id_key": "project_id_key",
        }

    def validate_upload(self, upload_path: str):
        logger.info(f"Starting internal math validation for upload: {upload_path}")

        try:
            if not Path(upload_path).exists():
                raise FileNotFoundError(f"File not found: {upload_path}")

            # Reading with data_only=True to attempt to see numbers instead of strings[cite: 2, 9]
            uploaded_df = pd.read_excel(
                upload_path, engine="openpyxl", engine_kwargs={"data_only": True}
            )

            # Ensure all financial columns are treated as float and NaNs are 0
            # This prevents math errors during internal summation
            fin_cols = [
                col
                for col in uploaded_df.columns
                if any(x in col for x in ["Appr", "Released", "Utilized"])
            ]
            for col in fin_cols:
                uploaded_df[col] = pd.to_numeric(
                    uploaded_df[col], errors="coerce"
                ).fillna(0.0)

            missing_headers = [
                h for h in self.display_to_db.keys() if h not in uploaded_df.columns
            ]
            if missing_headers:
                return False, f"Invalid Template. Missing headers: {missing_headers}"

            working_df = uploaded_df.rename(columns=self.display_to_db)
            error_list = []
            validated_rows = []

            for idx, row in working_df.iterrows():
                row_errors = self._check_row_rules(row, idx + 2)
                if row_errors:
                    error_row = uploaded_df.iloc[idx].to_dict()
                    error_row["Validation_Errors"] = " | ".join(row_errors)
                    error_list.append(error_row)
                else:
                    validated_rows.append(uploaded_df.iloc[idx])

            if error_list:
                return self._handle_failure(error_list)
            return self._handle_success(validated_rows)

        except Exception as e:
            logger.error(f"Critical Ingestion Error: {str(e)}")
            logger.error(traceback.print_exc())
            return False, f"System Error: {str(e)}"

    def _check_row_rules(self, row, excel_row_num):
        """
        Revised audit logic to explicitly calculate and report the shortfall amount.
        """
        errors = []
        try:
            key = row.get("project_id_key")

            # 1. Identity Verification[cite: 1]
            mpr_match = self.master_df[self.master_df["project_id_key"] == key]
            if mpr_match.empty:
                logger.error(f"Row {excel_row_num}: Project key '{key}' not found.")
                return [f"Row {excel_row_num}: Project Key mismatch."]

            mpr_row = mpr_match.iloc[0]

            # 2. Ratio Resolution[cite: 4]
            state_name = mpr_row["state_canonical"]
            comp = mpr_row["component"]
            ratio_tuple = get_ratio(state_name, comp)

            if not ratio_tuple:
                logger.warning(
                    f"Row {excel_row_num}: Missing ratio config for {state_name}/{comp}[cite: 4]."
                )
                return [f"Row {excel_row_num}: Ratio Configuration missing."]

            c_perc, s_perc = ratio_tuple  # e.g., 60, 40[cite: 4]

            # 3. Shortfall Quantification
            actual_cs_rel = row.get("uc_central_rel", 0)
            actual_ss_rel = row.get("uc_state_rel", 0)

            if c_perc > 0:
                # Step A: Find out what the state WAS supposed to release[cite: 8]
                expected_ss_rel = round((actual_cs_rel / c_perc) * s_perc, 2)

                # Step B: Calculate the actual difference (The Shortfall)[cite: 8]
                if actual_ss_rel < (expected_ss_rel - 0.01):
                    shortfall_amt = round(expected_ss_rel - actual_ss_rel, 2)

                    # Report the numeric gap explicitly for the consultant
                    error_msg = (
                        f"Shortfall Detected: State released {actual_ss_rel}, "
                        f"but based on Central release of {actual_cs_rel}, the State "
                        f"owed {expected_ss_rel}. Shortfall Amount: {shortfall_amt}"
                    )

                    errors.append(error_msg)
                    logger.debug(f"Row {excel_row_num}: {error_msg}.")

            # 4. Standard Integrity & Flow Checks[cite: 1]
            # Using internal sums to bypass uncalculated Excel formula cells[cite: 8]
            calc_total_appr = row["uc_central_appr"] + row["uc_state_appr"]
            calc_total_rel = row["uc_central_rel"] + row["uc_state_rel"]
            calc_total_util = row["uc_central_util"] + row["uc_state_util"]

            # Verify Master Approval Match[cite: 1, 8]
            if abs(calc_total_appr - mpr_row["mpr_total_appr"]) > 0.01:
                errors.append(
                    f"Approval Mismatch: Calculated Total ({calc_total_appr}) != Master MPR ({mpr_row['mpr_total_appr']})."
                )

            # Flow Logic[cite: 1, 8]
            if calc_total_rel > calc_total_appr:
                errors.append(
                    f"Flow Error: Total Released ({calc_total_rel}) > Approved ({calc_total_appr})."
                )

            if calc_total_util > calc_total_rel:
                errors.append(
                    f"Flow Error: Total Utilized ({calc_total_util}) > Released ({calc_total_rel})."
                )

        except Exception as e:
            logger.error(f"Row {excel_row_num}: Unexpected Validation Error: {str(e)}.")
            logger.error(traceback.print_exc())
            errors.append(f"System error on row {excel_row_num}.")

        return errors

    def _handle_failure(self, error_list):
        """
        Generates a professional, locked Annexure with text wrapping for specific columns.
        """
        error_df = pd.DataFrame(error_list)

        # 1. Drop internal ID for the State-facing report[cite: 1]
        if "project_id_key" in error_df.columns:
            error_df = error_df.drop(columns=["project_id_key"])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"data/review/Discrepancy_Report_{timestamp}.xlsx"
        Path("data/review").mkdir(parents=True, exist_ok=True)

        # Define columns that require wrapping to prevent overflow in locked cells
        wrap_cols = [
            "State",
            "District",
            "Component",
            "Institution Name",
            "Validation_Errors",
        ]

        with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
            error_df.to_excel(writer, index=False, sheet_name="Validation_Errors")
            sheet = writer.sheets["Validation_Errors"]

            # 2. Apply Formatting, Wrapping, and Protection
            # Every cell gets top alignment; only specific ones get wrap_text
            standard_top = Alignment(vertical="top")
            wrapped_top = Alignment(wrap_text=True, vertical="top")

            for col_idx, col_name in enumerate(error_df.columns, 1):
                col_letter = get_column_letter(col_idx)

                # Set Column Widths
                if col_name in wrap_cols:
                    sheet.column_dimensions[col_letter].width = 40
                    active_alignment = wrapped_top
                else:
                    sheet.column_dimensions[col_letter].width = 18
                    active_alignment = standard_top

                # Apply alignment to all data rows
                # row_idx starts at 2 to skip headers
                for row_idx in range(2, len(error_df) + 2):
                    sheet[f"{col_letter}{row_idx}"].alignment = active_alignment
            # 3. Lock the sheet
            sheet.protection.password = "RUSA_AUDIT_2026"
            sheet.protection.sheet = True
            sheet.protection.enable()

        logger.info(
            f"Annexure-ready Discrepancy Report generated: {report_path}[cite: 1]"
        )
        return False, report_path

    def _handle_success(self, validated_rows):
        success_df = pd.DataFrame(validated_rows)
        path = (
            f"data/verified/Verified_UC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        Path("data/verified").mkdir(parents=True, exist_ok=True)
        success_df.to_excel(path, index=False)
        return True, path


# Ratio Error: Central Approved should be 108000000.0.
# Shortfall: State Released (30000000.0) &lt; Expected (40000000.0). Gap: 10000000.0 | Flow Error: Total Utilized (99997693.0) &gt; Released (90000000.0).
