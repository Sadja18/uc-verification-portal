import logging
import os
import sys
import traceback

import pandas as pd

from services.template_generator import generate_consultant_template
from services.verification_engine import VerificationEngine

# Add current directory to path to allow importing services/mpr_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sys

from services.mpr_loader import (
    export_duplicate_projects,
    harmonize_and_merge_mpr,
    load_pmusha_mpr,
    load_rusa_mpr,
)


# Initialize logger
def setup_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger("MainApp")


logger = setup_logging()


def run_sprint_3_test(master_df):
    """
    Updated Sprint 3 Test: Uses the new VerificationEngine which
    internally resolves ratios via config.py.
    """
    logger.info("--- Starting UC Verification Pipeline: Sprint 3 (Validation) ---")
    
    try:
        # 1. Verification Check: Ensure Master Data exists
        if master_df is None or master_df.empty:
            logger.error("Master DataFrame not found. Run Sprint 1 first.")
            return

        # 2. Initialize the Engine 
        # Note: We no longer pass config_ratios; the engine handles it internally[cite: 5].
        engine = VerificationEngine(master_df=master_df)

        # 3. Define the Upload Path
        # This is the file the consultant has filled and "uploaded" back
        upload_file_path = "data/uploads/UC_Template_UTTAR_PRADESH_Filled.xlsx"

        if not os.path.exists(upload_file_path):
            logger.error(f"Test file missing: {upload_file_path}. Please place a filled template there.")
            return

        # 4. Execute the All-or-Nothing Validation Gate
        # This checks Approval match, Component ratios (MMER/EMDC), and Release/Util logic.
        success, result_path = engine.validate_upload(upload_file_path)

        # 5. Handle the All-or-Nothing Outcome[cite: 1]
        if success:
            print("\n" + "=" * 40)
            print("✅ VALIDATION SUCCESSFUL: All Rows Verified")
            print(f"Verified data exported to: {result_path}")
            print("=" * 40)
        else:
            print("\n" + "!" * 40)
            print("❌ VALIDATION FAILED")
            # The engine returns either a path to an Excel report or a string error[cite: 5].
            if isinstance(result_path, str) and result_path.endswith(".xlsx"):
                print(f"Discrepancy Report generated: {result_path}")
                print("Action: Fix the errors in the report and re-upload.")
            else:
                print(f"System/Header Error: {result_path}")
            print("!" * 40)

    except Exception as e:
        logger.error(f"Test Execution Failed: {e}")
        logger.debug(traceback.format_exc())
def run_sprint1():
    RUSA_PATH = "./data/RUSA_MPR_March.xlsx"
    PMUSHA_PATH = "./data/PM_USHA_MPR_March.xlsx"

    logger.info("--- Starting UC Verification Pipeline: Sprint 1 ---")

    try:
        # 1. Ingest with individual try/except boundaries
        try:
            df_rusa = load_rusa_mpr(RUSA_PATH)
        except Exception as e:
            logger.error(f"Failed to load RUSA file: {e}")
            return

        try:
            df_pmusha = load_pmusha_mpr(PMUSHA_PATH)
        except Exception as e:
            logger.error(f"Failed to load PM-USHA file: {e}")
            return

        # 2. Harmonize[cite: 1]
        master_df = harmonize_and_merge_mpr(df_rusa, df_pmusha)

        if master_df is None or master_df.empty:
            logger.error("Pipeline stopped: Master DataFrame is empty or null.")
            return

        if master_df is not None:
            # Export duplicates for review[cite: 1]
            review_file = export_duplicate_projects(master_df)

            if review_file:
                print(
                    f"Action Required: Duplicate projects found. Review: {review_file}"
                )
            else:
                print("Data Integrity Check: No duplicate projects found[cite: 1].")

        # 3. Final Success Report
        logger.info(f"SUCCESS: {len(master_df)} unique projects ready for Sprint 2.")
        print(f"Unified {len(master_df)} rows. Check logs/mpr_loader.log for details.")

        # master_df.to_excel("./data/MPR_March_Master.xlsx", index=False)
        return master_df

    except Exception as e:
        logger.critical(f"Unhandled pipeline failure: {e}")
        logger.debug(traceback.format_exc())


def run_sprint2(master_df):
    target_state = "UTTAR PRADESH"
    target_phase = "RUSA 2"
    output_file = f"data/templates/UC_Template_{target_state.replace(' ', '_')}.xlsx"

    success = generate_consultant_template(
        master_df, target_state, target_phase, output_file
    )

    if success:
        print(
            f"Template generated for {target_state}. Locked fields are Gray, Fillable are Green."
        )


if __name__ == "__main__":
    # run_sprint1()
    # run_sprint1()
    master_df = run_sprint1()

    if master_df is None or not isinstance(master_df, pd.DataFrame):
        logger.warning("empty df ")
        exit()

    # run_sprint2(master_df=master_df)

    run_sprint_3_test(master_df=master_df)
