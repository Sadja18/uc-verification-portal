# app.py
import traceback

import pandas as pd
import streamlit as st

from config import STATES_UTS, USERS, get_ratio
from mpr_loader import get_projects_for_state, load_mpr_data

# Page configuration
st.set_page_config(
    page_title="UC Verification Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def authenticate():
    """Handle login flow with error handling"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.error = None

    if not st.session_state.authenticated:
        st.title("🔐 UC Verification Portal")
        st.markdown("Please log in to continue.")

        # Display persistent error if any
        if st.session_state.error:
            st.error(f"⚠️ {st.session_state.error}")
            st.session_state.error = None  # Clear after display

        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                try:
                    if username in USERS and USERS[username]["password"] == password:
                        st.session_state.authenticated = True
                        st.session_state.user = username
                        st.session_state.role = USERS[username]["role"]
                        st.rerun()
                    else:
                        st.session_state.error = "Invalid username or password."
                        st.rerun()
                except Exception as e:
                    print(f"Error {e}")
                    st.session_state.error = "Login failed. Please try again."
                    # Log full error for debugging (visible in terminal)
                    print(f"[AUTH ERROR] {traceback.format_exc()}")
                    st.rerun()
        st.stop()


def handle_unexpected_error(func):
    """Decorator to wrap page handlers with global error catching"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            st.error(f"⚠️ Configuration error: Missing key {e}. Please contact admin.")
            print(f"[CONFIG KEYERROR] {traceback.format_exc()}")
        except FileNotFoundError as e:
            st.error(f"⚠️ File not found: {e}. Ensure data files are in place.")
            print(f"[FILE ERROR] {traceback.format_exc()}")
        except Exception as e:
            print(f"Error {e}")
            st.error(
                "⚠️ An unexpected error occurred. Please refresh or contact support."
            )
            print(f"[UNEXPECTED ERROR] {traceback.format_exc()}")

    return wrapper


@handle_unexpected_error
def admin_dashboard():
    """Admin view with safe config access"""
    st.subheader("🛡️ Admin Dashboard")
    try:
        st.info("✅ System Status: Active")
        st.markdown(f"📊 Loaded {len(STATES_UTS)} States/UTs from config.")
        st.markdown(
            "*(Admin features: MPR management, audit logs, ratio updates → P3)*"
        )
    except Exception:
        st.warning("⚠️ Could not load system stats. Config may be incomplete.")


@handle_unexpected_error
def consultant_workspace():
    """Consultant view: State selector → Download Template → Upload Filled UC"""
    st.subheader("👨‍💼 Consultant Workspace")
    st.markdown(
        "Select a State/UT to download the pre-populated UC template, fill it offline, and upload for verification."
    )

    # Ensure MPR is loaded (auto-loads from fixed path on first call)
    if "mpr_data" not in st.session_state or st.session_state.mpr_data is None:
        with st.spinner("🔄 Loading MPR data..."):
            mpr_df = load_mpr_data()
            
            print("mpr data loaded? ",mpr_df.head(1).to_dict(orient='records'))
            if mpr_df is not None:
                st.session_state.mpr_data = mpr_df
                st.session_state.mpr_ready = True
                st.success("✅ MPR data loaded and ready")
            else:
                st.session_state.mpr_ready = False
                st.warning("⚠️ MPR data unavailable. UC template generation disabled.")
                return  # Stop further rendering
    else:
        st.session_state.mpr_ready = True

    # State/UT Selector
    state = st.selectbox("📍 Select State/UT", STATES_UTS, index=0)

    # Show project count for transparency
    if st.session_state.mpr_ready:
        project_count = len(get_projects_for_state(st.session_state.mpr_data, state))
        st.caption(f"📊 {project_count} projects found for {state} in latest MPR")

    st.markdown("---")

    # Action Buttons (only enabled if MPR loaded)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download UC Template", use_container_width=True, disabled=not st.session_state.mpr_ready):
            if st.session_state.mpr_ready:
                with st.spinner("🔄 Generating UC template..."):
                    # Import here to avoid circular imports
                    from template_generator import generate_uc_template_bytes
                    
                    excel_bytes = generate_uc_template_bytes(
                        st.session_state.mpr_data, 
                        state
                    )
                    
                    if excel_bytes:
                        # Create safe filename
                        safe_state = state.replace(" ", "_").replace("/", "_")
                        filename = f"UC_Template_{safe_state}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
                        
                        st.download_button(
                            label="✅ Click to Download UC Template",
                            data=excel_bytes,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                        st.success("📥 Template ready! Fill the blank UC fields offline and upload for validation.")
                    else:
                        st.warning(f"⚠️ No projects found for {state} in MPR. Cannot generate template.")
            else:
                st.warning("⚠️ Please wait for MPR to load")
    
    with col2:
        if st.button("📤 Upload Filled UC", use_container_width=True, disabled=not st.session_state.mpr_ready):
            st.info("🔹 Upload & validation logic will be implemented in P2.3")

    # Helper note
    st.markdown(
        """
    <div style='background:#f0f2f6;padding:12px;border-radius:8px;margin-top:16px'>
    <strong>ℹ️ Workflow Reminder:</strong><br>
    1. Download template → 2. Fill UC fields offline → 3. Upload for validation → 4. Review flags → 5. Export verified data
    </div>
    """,
        unsafe_allow_html=True,
    )


def main():
    """Main router with session safety"""
    # Safety check: ensure session state is initialized
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Sidebar controls (only if authenticated)
    if st.session_state.authenticated:
        st.sidebar.title(f"👤 {st.session_state.user}")
        st.sidebar.markdown(f"**Role:** `{st.session_state.role}`")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            for key in ["authenticated", "user", "role", "error"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.title("📊 UC Verification Portal")

    # Role-based routing with error isolation
    if not st.session_state.authenticated:
        return  # authenticate() already called st.stop()

    try:
        if st.session_state.role == "Admin":
            admin_dashboard()
        elif st.session_state.role == "Consultant":
            consultant_workspace()
        else:
            st.error(f"⚠️ Unrecognized role: '{st.session_state.role}'. Contact admin.")
    except Exception as e:
        print(f"Error {e}")
        st.error("⚠️ Page failed to load. Please refresh or try again later.")
        print(f"[ROUTING ERROR] {traceback.format_exc()}")


if __name__ == "__main__":
    try:
        authenticate()
        main()
    except Exception as e:
        print(f"Error {e}")
        st.error("🚨 Critical startup error. Check terminal logs.")
        print(f"[STARTUP CRASH] {traceback.format_exc()}")
