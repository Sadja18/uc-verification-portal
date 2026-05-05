import logging
import os
import tempfile

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

from app.models import ValidationLog
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
            # Ensure state_canonical exists before accessing
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

    # Use a temporary file for robust Excel generation
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
        # Clean up temp file if it exists
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
def process_upload():
    """
    Handles the file upload and initial validation.
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
            # Save to temp directory
            temp_dir = os.path.join(current_app.root_path, "..", "data", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, file.filename)
            file.save(temp_path)

            # Before we run the verification engine
            # we should check if the state and rusa phase were already validated

            # 1. Uploaded Excel to pd.dataframe
            upload_df = pd.read_excel(temp_path, engine="openpyxl")

            # 2. Ensure State and RUSA phase columns
            if "State" not in upload_df.columns or "Phase" not in upload_df.columns:
                flash("Invalid template: Missing 'State' or 'Phase' columns.", "danger")

            # 3. Canonicalize state names, because why not
            # Canonicalize State Names
            upload_df["state_canonical"] = upload_df["State"].apply(
                normalize_state_name
            )
            # 4. Get unique valid combinations
            # We dropna to ignore empty rows if any
            combos = upload_df[['state_canonical', 'Phase']].dropna().drop_duplicates()
            
            # 5. Prepare lit of tuples for DB Query
            # Format [(state1, phase1), (state2, phase2)]
            combo_list = [tuple(row) for row in combos.itertuples(index=False)]
            
            # 6. Query DB for any existing SUCCESS logs for these combinations
            existing_successes = []
            for state, phase in combo_list:
                exists = ValidationLog.query.filter_by(
                    state=state,
                    phase=phase,
                    status='Success'
                ).first()
                if exists:
                    existing_successes.append(f"{state} - {phase}")
            
            # 7. If any combination was already successfully verified, BLOCK the upload
            if existing_successes:
                blocked_combos = ", ".join(existing_successes)
                flash(f"Upload Rejected: The following combinations have already been successfully verified and cannot be re-uploaded: {blocked_combos}. Please contact Admin to override.", "danger")
                return redirect(url_for("verifier.upload_uc_page"))
            
            # Run Verification Engine
            master_df = current_app.config.get("MASTER_DF")
            if master_df is None:
                raise Exception("Master Data not loaded in memory.")

            engine = VerificationEngine(master_df=master_df)

            # Validate
            success, result_path = engine.validate_upload(temp_path)

            preview_data = {
                "success": success,
                "result": [],  # Default empty list
                "filename": file.filename,
                "report_path": result_path,  # Keep original path for download button
            }

            # Check if the generated report exists before reading
            if result_path and os.path.exists(result_path):
                try:
                    # Read the Excel file generated by the engine
                    # This works for BOTH Success and Failure reports
                    df_result = pd.read_excel(result_path, engine="openpyxl")

                    # Convert to list of dicts for Jinja2 iteration
                    preview_data["result"] = df_result.to_dict("records")
                except Exception as e:
                    logger.error(f"Failed to read generated report for preview: {e}")
                    flash("Error generating preview data.", "warning")
            else:
                # Fallback if path is invalid or missing
                preview_data["result"] = []

            # Store formatted result in session
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

    # print(result_data)

    return render_template("preview.html", result=result_data)


@verifier.route("/download-discrepancy-report")
@login_required
def download_discrepancy_report():
    """
    Stub: Serves the discrepancy report generated during failure.
    TODO: Implement logic to retrieve the path from session/result and serve it.
    """
    # For now, just flash a message so you know it's hitting this route
    flash("Discrepancy Report download triggered (Stub).", "info")

    # In real implementation, you would do:
    # result = session.get('validation_result')
    # if result and not result['success']:
    #     return send_file(result['result'], as_attachment=True)

    return redirect(url_for("verifier.preview_results"))


@verifier.route("/commit-verification", methods=["POST"])
@login_required
def commit_verification():
    """
    Stub: Commits valid data to the database.
    TODO: Implement DB insertion logic using VerificationRecord model.
    """
    # For now, just flash a success message
    flash(
        "Verification committed successfully (Stub). Data would be saved to DB here.",
        "success",
    )

    # Clear the session data after commit
    session.pop("validation_result", None)

    return redirect(url_for("verifier.home"))


@verifier.route("/download-verified-excel")
@login_required
def download_verified_excel():
    """
    Stub: Allows downloading the clean Excel file before committing.
    TODO: Implement logic to generate/serve the clean Excel file.
    """
    flash("Verified Excel download triggered (Stub).", "info")

    # In real implementation, you would regenerate the clean Excel
    # or serve the one saved by _handle_success in VerificationEngine

    return redirect(url_for("verifier.preview_results"))
