# import logging
# import os
# import tempfile
# from datetime import datetime

# import pandas as pd
# from flask import (
#     Blueprint,
#     current_app,
#     flash,
#     redirect,
#     render_template,
#     request,
#     send_file,
#     session,
#     url_for,
# )
# from flask_login import current_user, login_required

# from app import db
# from app.models import ValidationLog, VerificationRecord
# from app.services.config import normalize_state_name
# from app.services.template_generator import generate_consultant_template
# from app.services.verification_engine import VerificationEngine

# # Setup specific logger for this blueprint
# logger = logging.getLogger("VerifierRoutes")

# verifier = Blueprint("verifier", __name__)


# @verifier.route("/")
# def home():
#     """
#     Home Page: Shows status of Master Data loading.
#     """
#     if not current_user.is_authenticated:
#         return redirect(url_for("auth.login"))
#     try:
#         master_df = current_app.config.get("MASTER_DF")

#         if master_df is not None and not master_df.empty:
#             data_status = "Loaded"
#             row_count = len(master_df)
#         else:
#             data_status = "Failed to Load"
#             row_count = 0
#             logger.warning("Master DF is empty or None on Home page load.")

#         return render_template("home.html", status=data_status, count=row_count)

#     except Exception as e:
#         logger.error(f"Critical error in Home route: {e}")
#         flash("System Error: Could not load application status.", "danger")
#         return render_template("home.html", status="Error", count=0)


# @verifier.route("/generate-template")
# @login_required
# def generate_template_page():
#     """
#     Renders the page where users select State/Phase to download a template.
#     """
#     try:
#         master_df = current_app.config.get("MASTER_DF")
#         states = []
#         phases = ["RUSA 1", "RUSA 2", "PM-USHA"]

#         if master_df is not None and not master_df.empty:
#             # Ensure state_canonical exists before accessing
#             if "state_canonical" in master_df.columns:
#                 states = sorted(master_df["state_canonical"].dropna().unique().tolist())

#         return render_template("generate_template.html", states=states, phases=phases)

#     except Exception as e:
#         logger.error(f"Error rendering generate template page: {e}")
#         flash("System Error: Could not load options.", "danger")
#         return redirect(url_for("verifier.home"))


# @verifier.route("/download-template", methods=["POST"])
# @login_required
# def download_template():
#     """
#     Handles the generation and download of the Excel Template.
#     """
#     state = request.form.get("state")
#     phase = request.form.get("phase")

#     if not state or not phase:
#         flash("Please select both State and Phase.", "danger")
#         return redirect(url_for("verifier.generate_template_page"))

#     master_df = current_app.config.get("MASTER_DF")
#     if master_df is None or master_df.empty:
#         logger.error("Template generation failed: Master DF missing.")
#         flash("System Error: Master Data not loaded.", "danger")
#         return redirect(url_for("verifier.home"))

#     # Use a temporary file for robust Excel generation
#     tmp_path = None
#     try:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
#             tmp_path = tmp.name

#         success = generate_consultant_template(master_df, state, phase, tmp_path)

#         if success:
#             logger.info(f"Template generated for {state} - {phase}. Sending file.")
#             return send_file(
#                 tmp_path,
#                 mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 as_attachment=True,
#                 download_name=f"UC_Template_{state.replace(' ', '_')}_{phase.replace(' ', '_')}.xlsx",
#             )
#         else:
#             logger.warning(f"No projects found for {state} - {phase}.")
#             flash(
#                 f"No projects found for {state} - {phase}. Please check selection.",
#                 "warning",
#             )
#             return redirect(url_for("verifier.generate_template_page"))

#     except Exception as e:
#         logger.error(f"Exception during template generation/download: {e}")
#         flash("An unexpected error occurred while generating the template.", "danger")
#         return redirect(url_for("verifier.generate_template_page"))

#     finally:
#         # Clean up temp file if it exists
#         if tmp_path and os.path.exists(tmp_path):
#             try:
#                 os.remove(tmp_path)
#             except OSError:
#                 pass


# @verifier.route("/upload-uc")
# @login_required
# def upload_uc_page():
#     """
#     Renders the file upload page.
#     """
#     return render_template("upload_uc.html")


# @verifier.route("/process-upload", methods=["POST"])
# def process_upload():
#     """
#     Handles the file upload and initial validation.
#     """
#     if "file" not in request.files:
#         flash("No file part", "danger")
#         return redirect(url_for("verifier.upload_uc_page"))

#     file = request.files["file"]
#     if file.filename == "":
#         flash("No selected file", "danger")
#         return redirect(url_for("verifier.upload_uc_page"))

#     if file and file.filename.endswith(".xlsx"):
#         temp_path = None
#         try:
#             # Save to temp directory
#             temp_dir = os.path.join(current_app.root_path, "..", "data", "temp")
#             os.makedirs(temp_dir, exist_ok=True)
#             temp_path = os.path.join(temp_dir, file.filename)
#             file.save(temp_path)

#             # Before we run the verification engine
#             # we should check if the state and rusa phase were already validated

#             # 1. Uploaded Excel to pd.dataframe
#             upload_df = pd.read_excel(temp_path, engine="openpyxl")

#             # 2. Ensure State and RUSA phase columns
#             if "State" not in upload_df.columns or "Phase" not in upload_df.columns:
#                 flash("Invalid template: Missing 'State' or 'Phase' columns.", "danger")

#             # 3. Canonicalize state names, because why not
#             # Canonicalize State Names
#             upload_df["state_canonical"] = upload_df["State"].apply(
#                 normalize_state_name
#             )
#             # 4. Get unique valid combinations
#             # We dropna to ignore empty rows if any
#             combos = upload_df[["state_canonical", "Phase"]].dropna().drop_duplicates()

#             # 5. Prepare lit of tuples for DB Query
#             # Format [(state1, phase1), (state2, phase2)]
#             combo_list = [tuple(row) for row in combos.itertuples(index=False)]

#             # 6. Query DB for any existing SUCCESS logs for these combinations
#             existing_successes = []
#             for state, phase in combo_list:
#                 exists = ValidationLog.query.filter_by(
#                     state=state, phase=phase, status="Success"
#                 ).first()
#                 if exists:
#                     existing_successes.append(f"{state} - {phase}")

#             # 7. If any combination was already successfully verified, BLOCK the upload
#             if existing_successes:
#                 blocked_combos = ", ".join(existing_successes)
#                 flash(
#                     f"Upload Rejected: The following combinations have already been successfully verified and cannot be re-uploaded: {blocked_combos}. Please contact Admin to override.",
#                     "danger",
#                 )
#                 return redirect(url_for("verifier.upload_uc_page"))

#             # Run Verification Engine
#             master_df = current_app.config.get("MASTER_DF")
#             if master_df is None:
#                 raise Exception("Master Data not loaded in memory.")

#             engine = VerificationEngine(master_df=master_df)

#             # Validate
#             success, result_path = engine.validate_upload(temp_path)

#             preview_data = {
#                 "success": success,
#                 "result": [],  # Default empty list
#                 "filename": file.filename,
#                 "report_path": result_path,  # Keep original path for download button
#             }

#             # Check if the generated report exists before reading
#             if result_path and os.path.exists(result_path):
#                 try:
#                     # Read the Excel file generated by the engine
#                     # This works for BOTH Success and Failure reports
#                     df_result = pd.read_excel(result_path, engine="openpyxl")

#                     # Convert to list of dicts for Jinja2 iteration
#                     preview_data["result"] = df_result.to_dict("records")
#                 except Exception as e:
#                     logger.error(f"Failed to read generated report for preview: {e}")
#                     flash("Error generating preview data.", "warning")
#             else:
#                 # Fallback if path is invalid or missing
#                 preview_data["result"] = []

#             # Store formatted result in session
#             session["validation_result"] = preview_data

#             return redirect(url_for("verifier.preview_results"))

#         except Exception as e:
#             logger.error(f"Validation Crash: {e}")
#             flash(f"An error occurred during validation: {str(e)}", "danger")
#             return redirect(url_for("verifier.upload_uc_page"))

#         finally:
#             # Cleanup temp upload file
#             if temp_path and os.path.exists(temp_path):
#                 try:
#                     os.remove(temp_path)
#                 except OSError:
#                     pass
#     else:
#         flash("Invalid file type. Please upload an .xlsx file.", "danger")
#         return redirect(url_for("verifier.upload_uc_page"))


# @verifier.route("/preview")
# @login_required
# def preview_results():
#     """
#     Displays the results of the validation.
#     """
#     result_data = session.get("validation_result")
#     if not result_data:
#         return redirect(url_for("verifier.upload_uc_page"))

#     # print(result_data)

#     return render_template("preview.html", result=result_data)


# @verifier.route("/download-discrepancy-report")
# @login_required
# def download_discrepancy_report():
#     """
#     Serves the discrepancy report generated during a failed validation.
#     Retrieves the file path from the session.
#     """
#     result_data = session.get("validation_result")

#     if not result_data:
#         flash("No validation data found in session.", "danger")
#         return redirect(url_for("verifier.upload_uc_page"))

#     if result_data["success"]:
#         flash(
#             "Cannot download discrepancy report for a successful validation.", "warning"
#         )
#         return redirect(url_for("verifier.preview_results"))

#     report_path = result_data.get("report_path")

#     if report_path and os.path.exists(report_path):
#         try:
#             return send_file(
#                 report_path,
#                 mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 as_attachment=True,
#                 download_name=f"Discrepancy_Report_{result_data.get('filename', 'upload')}.xlsx",
#             )
#         except Exception as e:
#             logger.error(f"Error serving discrepancy report: {e}")
#             flash("Error downloading report.", "danger")
#     else:
#         flash("Discrepancy report file not found on server.", "danger")

#     return redirect(url_for("verifier.preview_results"))


# @verifier.route("/commit-verification", methods=["POST"])
# @login_required
# def commit_verification():
#     """
#     Commits valid data to the Database (VerificationRecord & ValidationLog).
#     Implements the 'All-or-Nothing' rule.
#     """
#     result_data = session.get("validation_result")

#     if not result_data:
#         flash("No validation data found.", "danger")
#         return redirect(url_for("verifier.upload_uc_page"))

#     if not result_data["success"]:
#         flash("Cannot commit data with validation errors.", "danger")
#         return redirect(url_for("verifier.preview_results"))

#     try:
#         # 1. Extract Metadata
#         filename = result_data.get("filename", "unknown.xlsx")
#         user_id = current_user.id

#         # We need to identify the State/Phase for the Log.
#         # Since all rows in one upload belong to the same State/Phase (per template logic),
#         # we can peek at the first row of the result list.
#         records_list = result_data.get("result", [])
#         if not records_list:
#             flash("No records to commit.", "warning")
#             return redirect(url_for("verifier.home"))

#         first_row = records_list[0]
#         # Note: The keys here match the Display Names from Template Generator -> Engine Mapping
#         state = first_row.get("State")
#         phase = first_row.get("Phase")

#         if not state or not phase:
#             raise ValueError("Could not determine State/Phase from uploaded data.")

#         # 2. Start DB Transaction
#         # Create Validation Log Entry
#         log_entry = ValidationLog(
#             state=state,
#             phase=phase,
#             status="Success",
#             timestamp=datetime.utcnow(),
#             user_id=user_id,
#         )
#         db.session.add(log_entry)

#         # Create Verification Records
#         for row_dict in records_list:
#             # Map Display Names back to DB Column Names if necessary,
#             # or ensure VerificationRecord columns match the Excel headers exactly.
#             # Based on models.py, VerificationRecord uses specific column names.
#             # We assume the 'result' list from preview has keys matching the Excel Display Names.
#             # We must map them to the DB model fields.

#             # Helper to safely get float
#             def get_float(val):
#                 try:
#                     return float(val) if val is not None else 0.0
#                 except (ValueError, TypeError):
#                     return 0.0

#             record = VerificationRecord(
#                 project_id_key=row_dict.get(
#                     "project_id_key"
#                 ),  # This might be missing if dropped by engine, check engine code
#                 state_canonical=row_dict.get("State"),
#                 rusa_phase=row_dict.get("Phase"),
#                 component=row_dict.get("Component"),
#                 inst_name=row_dict.get("Institution Name"),
#                 uc_central_appr=get_float(row_dict.get("UC Central Appr.")),
#                 uc_state_appr=get_float(row_dict.get("UC State Appr.")),
#                 uc_total_appr=get_float(row_dict.get("UC Total Appr.")),
#                 uc_central_rel=get_float(row_dict.get("UC Central Released")),
#                 uc_state_rel=get_float(row_dict.get("UC State Released")),
#                 uc_total_rel=get_float(row_dict.get("UC Total Released")),
#                 uc_central_util=get_float(row_dict.get("UC Central Utilized")),
#                 uc_state_util=get_float(row_dict.get("UC State Utilized")),
#                 uc_total_util=get_float(row_dict.get("UC Total Utilized")),
#                 timestamp=datetime.utcnow(),
#                 user_id=user_id,
#             )
#             db.session.add(record)

#         # 3. Commit All
#         db.session.commit()

#         # 4. Cleanup Session
#         session.pop("validation_result", None)

#         flash(
#             f"Successfully committed {len(records_list)} records for {state} - {phase}.",
#             "success",
#         )
#         return redirect(url_for("verifier.home"))

#     except Exception as e:
#         db.session.rollback()
#         logger.error(f"Commit Failed: {e}")
#         flash(f"Database Error: Could not save records. {str(e)}", "danger")
#         return redirect(url_for("verifier.preview_results"))


# @verifier.route("/download-verified-excel")
# @login_required
# def download_verified_excel():
#     """
#     Allows downloading the clean Excel file generated by the engine before committing.
#     """
#     result_data = session.get("validation_result")

#     if not result_data:
#         flash("No validation data found.", "danger")
#         return redirect(url_for("verifier.upload_uc_page"))

#     if not result_data["success"]:
#         flash("Cannot download verified excel for failed validation.", "warning")
#         return redirect(url_for("verifier.preview_results"))

#     # The engine saves the success file to disk. We need to retrieve that path.
#     # However, our current process_upload only stores the 'report_path' for failures.
#     # For success, the engine returns True, path. We stored the path in 'report_path' key?
#     # Let's check process_upload: It stores result['report_path'] = result_path.

#     success_path = result_data.get("report_path")

#     if success_path and os.path.exists(success_path):
#         try:
#             return send_file(
#                 success_path,
#                 mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 as_attachment=True,
#                 download_name=f"Verified_UC_{result_data.get('filename', 'data')}.xlsx",
#             )
#         except Exception as e:
#             logger.error(f"Error serving verified excel: {e}")
#             flash("Error downloading file.", "danger")
#     else:
#         flash("Verified file not found on server.", "danger")

#     return redirect(url_for("verifier.preview_results"))
import io
import logging
import os
import tempfile
from datetime import datetime

import pandas as pd
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.models import ValidationLog, VerificationRecord
from app.routes.utils import admin_required
from app.services.config import normalize_state_name
from app.services.template_generator import generate_consultant_template
from app.services.verification_engine import VerificationEngine

# Setup specific logger for this blueprint
logger = logging.getLogger("VerifierRoutes")

verifier = Blueprint("verifier", __name__)


@verifier.route("/")
def home():
    """
    Home Page: Shows status of Master Data loading.
    Redirects to Login if not authenticated.
    """
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    try:
        master_df = current_app.config.get("MASTER_DF")

        if master_df is not None and not master_df.empty:
            data_status = "Loaded"
            row_count = len(master_df)
        else:
            data_status = "Failed to Load"
            row_count = 0
            logger.warning("Master DF is empty or None on Home page load.")

        return render_template("home.html", status=data_status, count=row_count)

    except Exception as e:
        logger.error(f"Critical error in Home route: {e}")
        flash("System Error: Could not load application status.", "danger")
        return render_template("home.html", status="Error", count=0)


@verifier.route("/generate-template")
@login_required
def generate_template_page():
    """
    Renders the page where users select State/Phase to download a template.
    """
    try:
        master_df = current_app.config.get("MASTER_DF")
        states = []
        phases = ["RUSA 1", "RUSA 2", "PM-USHA"]

        if master_df is not None and not master_df.empty:
            if "state_canonical" in master_df.columns:
                states = sorted(master_df["state_canonical"].dropna().unique().tolist())

        return render_template("generate_template.html", states=states, phases=phases)

    except Exception as e:
        logger.error(f"Error rendering generate template page: {e}")
        flash("System Error: Could not load options.", "danger")
        return redirect(url_for("verifier.home"))


@verifier.route("/download-template", methods=["POST"])
@login_required
def download_template():
    """
    Handles the generation and download of the Excel Template.
    """
    state = request.form.get("state")
    phase = request.form.get("phase")

    if not state or not phase:
        flash("Please select both State and Phase.", "danger")
        return redirect(url_for("verifier.generate_template_page"))

    master_df = current_app.config.get("MASTER_DF")
    if master_df is None or master_df.empty:
        logger.error("Template generation failed: Master DF missing.")
        flash("System Error: Master Data not loaded.", "danger")
        return redirect(url_for("verifier.home"))

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp_path = tmp.name

        success = generate_consultant_template(master_df, state, phase, tmp_path)

        if success:
            logger.info(f"Template generated for {state} - {phase}. Sending file.")
            return send_file(
                tmp_path,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=f"UC_Template_{state.replace(' ', '_')}_{phase.replace(' ', '_')}.xlsx",
            )
        else:
            logger.warning(f"No projects found for {state} - {phase}.")
            flash(
                f"No projects found for {state} - {phase}. Please check selection.",
                "warning",
            )
            return redirect(url_for("verifier.generate_template_page"))

    except Exception as e:
        logger.error(f"Exception during template generation/download: {e}")
        flash("An unexpected error occurred while generating the template.", "danger")
        return redirect(url_for("verifier.generate_template_page"))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@verifier.route("/upload-uc")
@login_required
def upload_uc_page():
    """
    Renders the file upload page.
    """
    return render_template("upload_uc.html")


@verifier.route("/process-upload", methods=["POST"])
@login_required
def process_upload():
    """
    Handles file upload, performs Gatekeeper Check, and runs Validation Engine.
    """
    if "file" not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("verifier.upload_uc_page"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(url_for("verifier.upload_uc_page"))

    if file and file.filename.endswith(".xlsx"):
        temp_path = None
        try:
            # 1. Save Upload
            temp_dir = os.path.join(current_app.root_path, "..", "data", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, file.filename)
            file.save(temp_path)

            # 2. GATEKEEPER CHECK START
            logger.info(f"Starting Gatekeeper Check for file: {file.filename}")

            # Read the whole file to check all combinations
            upload_df = pd.read_excel(temp_path, engine="openpyxl")

            if "State" not in upload_df.columns or "Phase" not in upload_df.columns:
                flash("Invalid Template: Missing 'State' or 'Phase' columns.", "danger")
                return redirect(url_for("verifier.upload_uc_page"))

            # Canonicalize State Names
            upload_df["state_canonical"] = upload_df["State"].apply(
                normalize_state_name
            )

            # Get unique valid combinations
            combos = upload_df[["state_canonical", "Phase"]].dropna().drop_duplicates()

            if combos.empty:
                flash("Upload file appears to be empty or invalid.", "danger")
                return redirect(url_for("verifier.upload_uc_page"))

            # Prepare list of tuples for DB query
            combo_list = [tuple(row) for row in combos.itertuples(index=False)]

            # Query DB for any existing SUCCESS logs for these combinations
            existing_successes = []
            for state, phase in combo_list:
                exists = ValidationLog.query.filter_by(
                    state=state, phase=phase, status="Success"
                ).first()
                if exists:
                    existing_successes.append(f"{state} - {phase}")

            # If any combination was already successfully verified, BLOCK the upload
            if existing_successes:
                blocked_combos = ", ".join(existing_successes)
                logger.warning(f"Upload Rejected by Gatekeeper: {blocked_combos}")
                flash(
                    f"Upload Rejected: The following combinations have already been successfully verified and cannot be re-uploaded: {blocked_combos}. Please contact Admin to override.",
                    "danger",
                )
                return redirect(url_for("verifier.upload_uc_page"))

            logger.info("Gatekeeper Check Passed. Proceeding to Verification Engine.")

            # 3. Run Verification Engine
            master_df = current_app.config.get("MASTER_DF")
            if master_df is None:
                raise Exception("Master Data not loaded in memory.")

            engine = VerificationEngine(master_df=master_df)

            # Validate -> Returns (bool, file_path_string)
            success, result_path = engine.validate_upload(temp_path)

            # --- CONVERSION LOGIC FOR PREVIEW.HTML ---
            preview_data = {
                "success": success,
                "result": [],
                "filename": file.filename,
                "report_path": result_path,
            }

            if result_path and os.path.exists(result_path):
                try:
                    df_result = pd.read_excel(result_path, engine="openpyxl")
                    preview_data["result"] = df_result.to_dict("records")
                except Exception as e:
                    logger.error(f"Failed to read generated report for preview: {e}")
                    flash("Error generating preview data.", "warning")

            session["validation_result"] = preview_data

            return redirect(url_for("verifier.preview_results"))

        except Exception as e:
            logger.error(f"Validation Crash: {e}")
            flash(f"An error occurred during validation: {str(e)}", "danger")
            return redirect(url_for("verifier.upload_uc_page"))

        finally:
            # Cleanup temp upload file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
    else:
        flash("Invalid file type. Please upload an .xlsx file.", "danger")
        return redirect(url_for("verifier.upload_uc_page"))


@verifier.route("/preview")
@login_required
def preview_results():
    """
    Displays the results of the validation.
    """
    result_data = session.get("validation_result")
    if not result_data:
        return redirect(url_for("verifier.upload_uc_page"))

    return render_template("preview.html", result=result_data)


@verifier.route("/download-discrepancy-report")
@login_required
def download_discrepancy_report():
    """
    Serves the discrepancy report generated during a failed validation.
    """
    result_data = session.get("validation_result")

    if not result_data:
        flash("No validation data found in session.", "danger")
        return redirect(url_for("verifier.upload_uc_page"))

    if result_data["success"]:
        flash(
            "Cannot download discrepancy report for a successful validation.", "warning"
        )
        return redirect(url_for("verifier.preview_results"))

    report_path = result_data.get("report_path")

    if report_path and os.path.exists(report_path):
        try:
            return send_file(
                report_path,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=f"Discrepancy_Report_{result_data.get('filename', 'upload')}.xlsx",
            )
        except Exception as e:
            logger.error(f"Error serving discrepancy report: {e}")
            flash("Error downloading report.", "danger")
    else:
        flash("Discrepancy report file not found on server.", "danger")

    return redirect(url_for("verifier.preview_results"))


@verifier.route("/commit-verification", methods=["POST"])
@login_required
def commit_verification():
    """
    Commits valid data to the Database (VerificationRecord & ValidationLog).
    Implements the 'All-or-Nothing' rule.
    """
    result_data = session.get("validation_result")

    if not result_data:
        flash("No validation data found.", "danger")
        return redirect(url_for("verifier.upload_uc_page"))

    if not result_data["success"]:
        flash("Cannot commit data with validation errors.", "danger")
        return redirect(url_for("verifier.preview_results"))

    try:
        # 1. Extract Metadata
        user_id = current_user.id

        records_list = result_data.get("result", [])
        if not records_list:
            flash("No records to commit.", "warning")
            return redirect(url_for("verifier.home"))

        first_row = records_list[0]
        state = first_row.get("State")
        phase = first_row.get("Phase")

        if not state or not phase:
            raise ValueError("Could not determine State/Phase from uploaded data.")

        logger.info(
            f"Committing {len(records_list)} records for {state} - {phase} by User {user_id}"
        )

        # 2. Start DB Transaction
        log_entry = ValidationLog(
            state=state,
            phase=phase,
            status="Success",
            timestamp=datetime.utcnow(),
            user_id=user_id,
        )
        db.session.add(log_entry)

        # Helper to safely get float
        def get_float(val):
            try:
                return float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                return 0.0

        # Create Verification Records
        for row_dict in records_list:
            record = VerificationRecord(
                project_id_key=row_dict.get("project_id_key"),
                state_canonical=row_dict.get("State"),
                rusa_phase=row_dict.get("Phase"),
                component=row_dict.get("Component"),
                inst_name=row_dict.get("Institution Name"),
                uc_central_appr=get_float(row_dict.get("UC Central Appr.")),
                uc_state_appr=get_float(row_dict.get("UC State Appr.")),
                uc_total_appr=get_float(row_dict.get("UC Total Appr.")),
                uc_central_rel=get_float(row_dict.get("UC Central Released")),
                uc_state_rel=get_float(row_dict.get("UC State Released")),
                uc_total_rel=get_float(row_dict.get("UC Total Released")),
                uc_central_util=get_float(row_dict.get("UC Central Utilized")),
                uc_state_util=get_float(row_dict.get("UC State Utilized")),
                uc_total_util=get_float(row_dict.get("UC Total Utilized")),
                timestamp=datetime.utcnow(),
                user_id=user_id,
            )
            db.session.add(record)

        # 3. Commit All
        db.session.commit()
        logger.info("Database Commit Successful.")

        # 4. Cleanup Session
        session.pop("validation_result", None)

        flash(
            f"Successfully committed {len(records_list)} records for {state} - {phase}.",
            "success",
        )
        return redirect(url_for("verifier.home"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Commit Failed: {e}")
        flash(f"Database Error: Could not save records. {str(e)}", "danger")
        return redirect(url_for("verifier.preview_results"))


@verifier.route("/download-verified-excel")
@login_required
def download_verified_excel():
    """
    Allows downloading the clean Excel file generated by the engine before committing.
    """
    result_data = session.get("validation_result")

    if not result_data:
        flash("No validation data found.", "danger")
        return redirect(url_for("verifier.upload_uc_page"))

    if not result_data["success"]:
        flash("Cannot download verified excel for failed validation.", "warning")
        return redirect(url_for("verifier.preview_results"))

    success_path = result_data.get("report_path")

    if success_path and os.path.exists(success_path):
        try:
            return send_file(
                success_path,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=f"Verified_UC_{result_data.get('filename', 'data')}.xlsx",
            )
        except Exception as e:
            logger.error(f"Error serving verified excel: {e}")
            flash("Error downloading file.", "danger")
    else:
        flash("Verified file not found on server.", "danger")

    return redirect(url_for("verifier.preview_results"))


@verifier.route("/admin/global-export")
@login_required
@admin_required
def global_export():
    """
    Admin-only route to download all verified records as an Excel file.
    Includes audit trail metadata (User, Timestamp).
    """
    try:
        # Query all verified records, ordered by timestamp (newest last)
        records = VerificationRecord.query.order_by(
            VerificationRecord.timestamp.asc()
        ).all()

        if not records:
            flash("No verified records found in the database.", "warning")
            return redirect(url_for("verifier.home"))

        # Convert SQLAlchemy objects to list of dicts
        data = []
        for rec in records:
            # Fetch username for audit trail
            uploader_username = "Unknown"
            if rec.uploader:
                uploader_username = rec.uploader.username

            data.append(
                {
                    "Timestamp": rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Uploaded By": uploader_username,
                    "State": rec.state_canonical,
                    "Phase": rec.rusa_phase,
                    "Component": rec.component,
                    "Institution": rec.inst_name,
                    "Project Key": rec.project_id_key,
                    # UC Financials
                    "UC Central Appr": rec.uc_central_appr,
                    "UC State Appr": rec.uc_state_appr,
                    "UC Total Appr": rec.uc_total_appr,
                    "UC Central Released": rec.uc_central_rel,
                    "UC State Released": rec.uc_state_rel,
                    "UC Total Released": rec.uc_total_rel,
                    "UC Central Utilized": rec.uc_central_util,
                    "UC State Utilized": rec.uc_state_util,
                    "UC Total Utilized": rec.uc_total_util,
                }
            )

        # Create DataFrame
        df_export = pd.DataFrame(data)

        # Write to BytesIO (in-memory file)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Verified_UCs")

        output.seek(0)

        logger.info(
            f"Global Export downloaded by Admin {current_user.username}. Rows: {len(records)}"
        )

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"Global_Verified_UC_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )

    except Exception as e:
        logger.error(f"Global Export Failed: {e}")
        flash("An error occurred while generating the export.", "danger")
        return redirect(url_for("verifier.home"))
