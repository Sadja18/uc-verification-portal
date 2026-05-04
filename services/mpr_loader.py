import logging
import os
import traceback
from typing import Dict, Optional, Tuple

import pandas as pd

import config


# --- Logging Configuration ---
def setup_logger():
    """Sets up logger to write to logs/mpr_loader.log"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("MPRLoader")
    logger.setLevel(logging.DEBUG)

    # File Handler
    fh = logging.FileHandler(os.path.join(log_dir, "mpr_loader.log"))
    fh.setLevel(logging.DEBUG)

    # Console Handler (for immediate feedback during dev)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = setup_logger()


def load_rusa_mpr(file_path: str) -> pd.DataFrame:
    """
    Loads RUSA MPR Excel file.
    Args:
        file_path: Path to RUSA MPR Excel file.
    Returns:
        Pandas DataFrame with stripped column names.
    Raises:
        FileNotFoundError: If file does not exist.
        Exception: If loading fails.
    """
    logger.info(f"Loading RUSA MPR from: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"RUSA MPR file not found at {file_path}")

    try:
        # Load using openpyxl engine as requested
        df = pd.read_excel(file_path, engine="openpyxl", sheet_name="data")

        # Strip whitespace from column names to avoid key errors
        df.columns = df.columns.str.strip()

        if "State" not in df.columns:
            raise ValueError(
                "Column 'State' not found in RUSA MPR. Check header names."
            )
        # FIX 2: Force Year to string if it exists
        if "Year" in df.columns:
            df["Year"] = (
                pd.to_numeric(df["Year"], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
            )

        # Financial Coercion Delta
        financial_cols = [
            "Central Share Approved",
            "Central Share Released",
            "Central Share Utilised",
            "State Share Approved",
            "State Share Released",
            "State Share Utilised",
            "Total Amount Approved",
            "Total Amount Released",
            "Total Amount Utilised",
        ]
        for col in financial_cols:
            if col in df.columns:
                df[col] = (
                    pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)
                )

        # Ensure 'State' column exists

        logger.info(f"Successfully loaded RUSA MPR. Shape: {df.shape}")
        return df

    except Exception as e:
        logger.error(f"Error loading RUSA MPR: {str(e)}")
        raise


def load_pmusha_mpr(file_path: str) -> pd.DataFrame:
    logger.info(f"Loading PM-USHA MPR from: {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"PM-USHA MPR file not found at {file_path}")

    try:
        # Load using openpyxl engine
        logger.info(f"Loading mpr file as df {file_path}")
        df = pd.read_excel(
            file_path,
            engine="openpyxl",
            sheet_name="data",
            dtype=str,
            keep_default_na=False,
            na_values=[],
            verbose=True,
        )
        logger.info(f"loaded mpr file as df {file_path}")

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Ensure 'State' column exists
        if "State" not in df.columns:
            raise ValueError(
                "Column 'State' not found in PM-USHA MPR. Check header names."
            )

        # FIX 2: Force Year to string if it exists
        if "Year" in df.columns:
            df["Year"] = (
                pd.to_numeric(df["Year"], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
            )

        # --- FIX FOR NaN INT ERROR ---
        # Define financial columns that might contain NaNs
        financial_cols = [
            "Central Share Amount Approved",
            "Central Share Amount Released",
            "Central Share Amount Utilised",
            "State Share Amount Approved",
            "State Share Amount Released",
            "State Share Amount Utilised",
            "Total Amount Approved",
            "Total Amount Released",
            "Total Amount Utilised",
        ]

        # Convert only existing financial columns to float64 to handle NaNs safely
        for col in financial_cols:
            if col in df.columns:
                logger.debug(f"Column {col} to coerce into numeric")
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

        logger.info(f"Successfully loaded PM-USHA MPR. Shape: {df.shape}")
        return df

    except Exception as e:
        logger.error(f"Error loading PM-USHA MPR: {str(e)}")
        raise


def validate_state_names(df: pd.DataFrame, source_name: str) -> Dict[str, str]:
    """
    Checks if all unique states in the DF can be mapped to canonical names.
    Args:
        df: Pandas DataFrame containing a 'State' column.
        source_name: Name of the source (e.g., "RUSA MPR") for logging.

    Returns:
        Dictionary of {raw_state_name: "Unmapped"} for states not found in config.
    """
    if "State" not in df.columns:
        logger.error(f"'State' column missing in {source_name}")
        return {}

    # Get unique non-null states
    unique_raw_states = df["State"].dropna().unique()
    unmapped = {}

    logger.info(
        f"Validating {len(unique_raw_states)} unique states in {source_name}..."
    )

    for raw_state in unique_raw_states:
        raw_str = str(raw_state).strip()
        if not raw_str:
            continue

        # Normalize using config helper
        canonical = config.normalize_state_name(raw_str)

        logger.debug(f"raw state {raw_state} : canonical {canonical}")

        # Check if the normalized name is in our list of known canonical states
        if canonical not in config.STATES_UTS:
            unmapped[raw_str] = "Not found in config.STATES_UTS"

    if unmapped:
        logger.warning(
            f"{source_name}: Found {len(unmapped)} unmapped states: {list(unmapped.keys())}"
        )
    else:
        logger.info(f"{source_name}: All states mapped successfully.")

    return unmapped


def load_all_mpr_data(
    rusa_path: str, pmusha_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    """
    Wrapper to load both MPR files and validate state names.

    Args:
        rusa_path: Path to RUSA MPR Excel file.
        pmusha_path: Path to PM-USHA MPR Excel file.

    Returns:
        Tuple: (df_rusa, df_pmusha, combined_unmapped_states_dict)
    """
    logger.info("Starting MPR Data Load Process...")

    # 1. Load RUSA
    df_rusa = load_rusa_mpr(rusa_path)
    unmapped_rusa = validate_state_names(df_rusa, "RUSA MPR")

    # 2. Load PM-USHA
    df_pmusha = load_pmusha_mpr(pmusha_path)
    unmapped_pmusha = validate_state_names(df_pmusha, "PM-USHA MPR")

    # 3. Combine Unmapped States
    combined_unmapped = {**unmapped_rusa, **unmapped_pmusha}

    if combined_unmapped:
        logger.warning(
            f"Total Unmapped States: {len(combined_unmapped)}. Please update config.py."
        )
        logger.warning(f"Unmapped List: {list(combined_unmapped.keys())}")
    else:
        logger.info("All states in both files are mapped correctly.")

    logger.info("MPR Data Load Process Completed.")

    return df_rusa, df_pmusha, combined_unmapped


def generate_composite_key(row: pd.Series) -> str:
    """Generates the 5-part unique project identifier."""
    try:
        parts = [
            str(row.get("state_canonical", "")),
            str(row.get("rusa_phase", "")),
            str(row.get("component", "")),
            str(row.get("District", "")),
            str(row.get("inst_name", "")),
            str(row.get("pab_no", "")),
        ]
        key = "|".join([p.strip().upper() for p in parts])
        # if str(parts[0]).upper() in [
        #     "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
        #     "BIHAR",
        #     "SIKKIM",
        #     "KARNATAKA",
        # ] and str(parts[2]).upper() in [
        #     "PREPARATORY GRANTS",
        #     "NEW MODEL DEGREE COLLEGES",
        # ]:
        #     logger.debug(f"Row is {parts} key is {key}")
        # Standardize: uppercase and strip to ensure 'RUSA 1' matches 'rusa 1'[cite: 1]
        return key
    except Exception as e:
        logger.error(
            f"Failed to generate composite key for row: {row.get('inst_name', 'Unknown')}. Error: {e}"
        )
        return "INVALID_KEY"


def harmonize_and_merge_mpr(
    df_rusa: pd.DataFrame, df_pmusha: pd.DataFrame
) -> Optional[pd.DataFrame]:
    """Standardizes headers, applies canonical logic, and merges into a Master DataFrame[cite: 1, 4]."""
    logger.info("Starting MPR Harmonization Delta...")

    try:
        # Mapping Dictionary based on technical requirements[cite: 1]
        rusa_map = {
            "State": "state_raw",
            "RUSA Phase": "rusa_phase",
            "Component Name": "component",
            "Institution Name": "inst_name",
            "PAB Meeting Number": "pab_no",
            "PAB Date": "pab_date",
            "Months": "mpr_month",  # FIX 1: Harmonized Month
            "Percentage Physical Progress Total": "mpr_phys_progress_pct",  # FIX 3: Harmonized Progress
            # Approved (You already have these)
            "Central Share Approved": "mpr_central_appr",
            "State Share Approved": "mpr_state_appr",
            "Total Amount Approved": "mpr_total_appr",
            # Released (MISSING IN YOUR CURRENT CODE)
            "Central Share Released": "mpr_central_rel",
            "State Share Released": "mpr_state_rel",
            "Total Amount Released": "mpr_total_rel",
            # Utilized (MISSING IN YOUR CURRENT CODE)
            "Central Share Utilised": "mpr_central_util",
            "State Share Utilised": "mpr_state_util",
            "Total Amount Utilised": "mpr_total_util",
        }

        pmusha_map = {
            "State": "state_raw",
            "RUSA Phase": "rusa_phase",
            "Component Name": "component",
            "Institution Name": "inst_name",
            "PAB Meeting Number": "pab_no",
            "PAB Date": "pab_date",
            "Month": "mpr_month",  # FIX 1: Harmonized Month
            "Physical Progress (Overall Project)(%)": "mpr_phys_progress_pct",  # FIX 3: Harmonized Progress
            # Approved (You already have these)
            "Central Share Amount Approved": "mpr_central_appr",
            "State Share Amount Approved": "mpr_state_appr",
            "Total Amount Approved": "mpr_total_appr",
            # Released (MISSING IN YOUR CURRENT CODE)
            "Central Share Amount Released": "mpr_central_rel",
            "State Share Amount Released": "mpr_state_rel",
            "Total Amount Released": "mpr_total_rel",
            # Utilized (MISSING IN YOUR CURRENT CODE)
            "Central Share Amount Utilised": "mpr_central_util",
            "State Share Amount Utilised": "mpr_state_util",
            "Total Amount Utilised": "mpr_total_util",
        }

        # Process RUSA
        logger.info("Harmonizing RUSA DataFrame...")
        df_rusa = df_rusa.rename(columns=rusa_map)

        # Process PM-USHA
        logger.info("Harmonizing PM-USHA DataFrame...")
        df_pmusha = df_pmusha.rename(columns=pmusha_map)

        # Combine
        master_df = pd.concat([df_rusa, df_pmusha], ignore_index=True)

        # Apply State Normalization[cite: 3, 5]
        logger.info("Applying state name normalization...")
        master_df["state_canonical"] = master_df["state_raw"].apply(
            config.normalize_state_name
        )

        # Generate Composite Keys[cite: 1]
        logger.info("Generating composite project keys...")
        master_df["project_id_key"] = master_df.apply(generate_composite_key, axis=1)

        # Remove and log invalid keys
        invalid_mask = master_df["project_id_key"] == "INVALID_KEY"
        if invalid_mask.any():
            logger.warning(
                f"Discarding {invalid_mask.sum()} rows due to key generation failure."
            )
            master_df = master_df[~invalid_mask]

        # Duplicate Detection[cite: 1]
        dupes = master_df[master_df.duplicated("project_id_key", keep=False)]
        if not dupes.empty:
            logger.warning(
                f"Found {len(dupes)} rows with duplicate project keys. Check source data."
            )
            for key in dupes["project_id_key"].unique()[:5]:  # Log first 5 examples
                logger.debug(f"Duplicate Key Example: {key}")

        # --- NEW: DUPLICATE REMOVAL LOGIC ---
        # Identify duplicates before removing them for logging purposes
        duplicate_count = master_df.duplicated("project_id_key", keep=False).sum()

        if duplicate_count > 0:
            logger.warning(
                f"Found {duplicate_count} duplicate rows. Keeping the last occurrence."
            )

            # Keep 'last' ensures the most recent entry in the Excel is preserved
            master_df = master_df.drop_duplicates(
                subset=["project_id_key"], keep="last"
            )

            logger.info(
                f"Duplicates removed. New row count: {len(master_df)}[cite: 1]."
            )
        else:
            logger.info("No duplicates detected in the master dataset[cite: 1].")

        logger.info(f"Harmonization complete. Final Master Row Count: {len(master_df)}")
        return master_df

    except Exception as e:
        logger.error(f"Critical error during harmonization: {e}")
        logger.error(traceback.format_exc())
        return None


def export_duplicate_projects(
    master_df: pd.DataFrame, output_dir: str = "data/review"
) -> str:
    """
    Identifies rows with non-unique project keys and exports them to Excel.
    Returns the path to the generated file.
    """
    try:
        # Create review directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created directory for review files: {output_dir}")

        # Find all rows that share a key with at least one other row
        duplicate_mask = master_df.duplicated(subset=["project_id_key"], keep=False)
        df_duplicates = master_df[duplicate_mask].copy()

        if df_duplicates.empty:
            logger.info("No duplicate project keys found. Export skipped.")
            return ""

        # Sort by key so duplicates are grouped together for easier review
        df_duplicates.sort_values(by="project_id_key", inplace=True)

        # Generate timestamped filename
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_dir, f"duplicate_projects_{timestamp}.xlsx")

        # Export to Excel
        df_duplicates.to_excel(file_path, index=False, engine="openpyxl")
        logger.warning(f"Exported {len(df_duplicates)} duplicate rows to {file_path}.")

        return file_path

    except Exception as e:
        logger.error(f"Failed to export duplicate projects: {e}")
        logger.debug(traceback.format_exc())
        return ""
