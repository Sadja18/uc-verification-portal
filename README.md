# UC Verification Portal

A streamlined web application for validating Utilization Certificates (UCs) for **RUSA** and **PM-USHA** projects. This tool automates the verification of financial ratios, fund flow logic, and approval matches against Master Monthly Progress Reports (MPR), ensuring data integrity before final commitment.

## 🚀 Key Features

- **Automated Template Generation:** Downloads pre-populated Excel templates with locked MPR data and fillable UC fields.
- **Smart Validation Engine:**
  - Checks **State/Central Share Ratios** dynamically based on State and Component.
  - Validates **Fund Flow Logic** (Released ≤ Approved, Utilized ≤ Released).
  - Ensures **Approval Matches** between UC and Master MPR.
- **Gatekeeper Logic:** Prevents duplicate successful submissions for the same State/Phase combination.
- **Audit Trail:** Logs every upload attempt and stores verified records with user attribution.
- **Admin Controls:** Global export of all verified records and user management.

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, Flask, SQLAlchemy (SQLite)
- **Data Processing:** Pandas, Openpyxl
- **Frontend:** Jinja2, Bootstrap 5.3, DataTables.js
- **Authentication:** Flask-Login (Role-based: Consultant/Admin)

## 📂 Project Structure

```text
uc-verification-exercise/
├── app/
│   ├── __init__.py          # App factory, DB init, MPR loading
│   ├── models.py            # User, ValidationLog, VerificationRecord
│   ├── routes/
│   │   ├── auth.py          # Login/Logout
│   │   └── verifier.py      # Core verification routes
│   ├── services/
│   │   ├── config.py        # State ratios & canonicalization
│   │   ├── mpr_loader.py    # ETL for RUSA/PM-USHA files
│   │   ├── template_generator.py # Excel template creation
│   │   └── verification_engine.py # Validation logic
│   └── templates/           # HTML UI
├── data/
│   ├── master/              # Source MPR Excel Files
│   ├── temp/                # Uploads
│   ├── review/              # Discrepancy Reports
│   └── verified/            # Clean Verified Files
├── logs/                    # Application logs
├── run.py                   # CLI commands & entry point
├── requirements.txt
└── README.md
```

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip

### Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd uc-verification-exercise
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Data Directory**
   Place your source MPR files in `data/master/`:
   - `RUSA_MPR_March.xlsx`
   - `PM_USHA_MPR_March.xlsx`

4. **Initialize Database & Folders**
   ```bash
   flask init-db
   ```
   *This creates `uc_audit.db` and necessary directories (`data/temp`, `logs`, etc.).*

5. **Create Admin User**
   ```bash
   flask create-user admin secret123 --role admin
   ```

6. **Run the Application**
   ```bash
   flask run
   ```
   Access the portal at `http://127.0.0.1:5000`

## 👤 User Guide

### For Consultants

1. **Login:** Use your provided username and password.
2. **Generate Template:**
   - Select **State/UT** and **Scheme Phase** (RUSA 1/2 or PM-USHA).
   - Click **Generate & Download Excel**.
   - The downloaded file contains locked gray cells (MPR data) and green fillable cells (UC data).
3. **Fill Data:** Enter UC Approved, Released, and Utilized amounts in the green cells. *Do not modify gray cells.*
4. **Upload & Verify:**
   - Go to **Verify UC Details**.
   - Upload the filled Excel file.
   - Review the **Preview Page**:
     - **Green Rows:** Valid data.
     - **Red Rows:** Errors (e.g., Ratio Shortfall, Flow Logic Error).
5. **Resolve Errors:**
   - If errors exist, click **Download Discrepancy Report**, fix the Excel file, and re-upload.
6. **Commit:**
   - If no errors, click **Submit & Save to Master**. This permanently saves the data and locks the State/Phase combination from future uploads.

### For Admins

1. **Global Export:**
   - Click the **📥 Global Export** link in the navbar.
   - Downloads an Excel file containing all successfully verified records from the database, including audit metadata (Uploader, Timestamp).
2. **User Management:**
   - Create new consultant accounts via CLI:
     ```bash
     flask create-user consultant1 pass123 --role consultant
     ```

## 🔍 Validation Rules

The engine enforces the following rules per row:

1. **Identity Check:** Project Key must exist in Master MPR.
2. **Ratio Shortfall:**
   - Calculates `Expected State Release` based on `Central Release` and configured `CS:SS Ratio`.
   - Flags if `Actual State Release < Expected State Release`.
3. **Approval Match:**
   - `UC Central Approved + UC State Approved` must equal `Master MPR Total Approved`.
4. **Flow Logic:**
   - `Total Released ≤ Total Approved`
   - `Total Utilized ≤ Total Released`

## 📝 Configuration

### State Ratios (`app/services/config.py`)
Ratios are defined in the `CS_SS_RATIOS` dictionary. Example:
```python
"Uttar Pradesh": {
    "Other": (60, 40),  # 60% Central, 40% State
    "MMER": (100, 0),   # 100% Central
}
```
*If a state/component combination is missing, it defaults to (60, 40).*

### State Canonicalization
The `STATE_VARIANTS` dictionary maps messy input names (e.g., "U.P.", "Orissa") to canonical names (e.g., "Uttar Pradesh", "Odisha") for consistent database storage.

## 🐞 Troubleshooting

- **"Master DataFrame is empty":** Ensure `RUSA_MPR_March.xlsx` and `PM_USHA_MPR_March.xlsx` exist in `data/master/` and contain a sheet named `data`.
- **"Upload Rejected: Already Verified":** The State/Phase combination was previously committed. Only Admins can override this by manually clearing the `ValidationLog` (not recommended for audit integrity).
- **"Ratio Configuration Missing":** Add the missing State/Component ratio to `app/services/config.py`.

## 📄 License

[LICENSE](LICENSE)