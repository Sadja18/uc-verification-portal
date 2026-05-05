# UC Verification Exercise

## Background:

- Projects are approved for given State/UT and Institution under RUSA and PM-USHA during various Project Approval Board Mettings (PAB Meeting).
- The implementing agency fills Monthyl Progress Report (MPR) for given project; combination of State/UT + RUSA Phase + Component Name + Institution Name + PAB meeting number
- The approved amount, released amount and utilised amount are filled in each MPR under following:
    - Central Share
    - State Share
    - Total Share
- For each State/UT + Component Name: there is a fixed ratio for Central Share : State Share
- If State Share Released entry in an MPR is less than the State Share Expected Released calculated based on ratio of Central Share: State Share for a given project; then the difference in `State Share Release Expected` - `State Share Released` is called a shortfall.
- `Single Nodal Agency` (SNA) is the foundational model for managing `Centrally Sponsored Scheme` (CSS) funds.
- `SNA SPARSH` (SAMAYOCHIT PRANALI EKIKRUT SHIGHRA HASTANTARAN) is an enhanced, "true Just-in-Time" (JIT) upgrade launched in January 2024
- Some projects approved earlier in RUSA and PM-USHA were originally funded through SNA model.
- All States/UTs were onboarded on SNA SPARSH model in phased manner with a batch of States/UTs at a time. And when all projects in a given State/UT were onboarded, the State/UT was considered that it was onboarded
- As on January 2026, all projects are onboarded in SNA SPARSH model.
- Utilization Certificate (UC) is sent by the State/UT for each project when the issued fund installments; also known as Mother Sanctions `MS` are exhausted.
- In a given FY, one or more MS are issued for each of the State/UT under RUSA/PM-USHA.

The UC verification exercise is to be done for the first UC provided by the State/UT just after they were onboarded on SPARSH model.

This portal would allow consultants of the RUSA/PM-USHA section to do a verification to do following:

- Take the UC issued after a given project was onboarded in SNA SPARSH
- Find the values for Approved Amounts, Released Amounts, Utilised Amounts for Central Share, State Share and Total (Central Share + State Share)
- The latest MPR would be downloaded as an excel file and would be part of portal.
- On portal, there would be a option for user to select a State/UT and download projects UC template with following: 
    - Pre-populated fields to come from latest MPR:
        - State/UT
        - Component Name
        - RUSA Phase (RUSA 1/ RUSA 2/ PM-USHA)
        - District
        - Institution Name 
        - PAB Date
        - PAB Meeting Number
        - Total Amount Approved
        - Central Share Approved
        - State Share Approved
    - Blank fields which the user would fill after downloading:
        - Total Amount Approved (UC)
        - Central Share Amount Approved (UC)
        - State Share Amount Approved (UC)
        - Total Amount Released (UC)
        - Central Share Amount Released (UC)
        - State Share Amount Released (UC)
        - Total Amount Utilised (UC)
        - Central Share Amount Utilised (UC)
        - State Share Amount Utilised (UC) 
- On second user interface of portal, the user would upload the completely filled UC for a given State/UT
- First stage of validation for amounts would be Approved(UC) >= Released(UC) >= Utilised(UC) for all three shares.
- Second stage of validation for amounts would be:
    - Approved (MPR) >= Approved (UC)
    - Released (MPR) >= Released (UC)
    - Utilised (MPR) >= Utilised (UC)
- The preview pane would then flag discrepancy:
    - Amount mismatch
    - State Share shortfall
- If there are no flags, show success and option to append the updated data to a excel file
- If there are discrepancies, allow download as excel for internal offline review. The downloaded excel would have a new column mentioning the flags for discrepancy. If there is one or more flags in a row, that cell would have all the flags in human readable format.

---

## Part 1
Since the project is small and the entire verification exercise is a one time activity, I was wondering following:

1. Which tech stack should I go with:
- Django seems like an overkill
- Google App script is an option, but the amount of boilerplate and other code to write; and lack of login flow makes my head spin
- Flask is viable, but would need to create SQLite3 handler, and would need to discuss RBAC account managers (there are only two but still)

App Script would allow me to make the site online with no server. and the appended file of validated projects would be google sheet, easier to review

Other Approaches involving framework would require me to upload/append the output file to drive:
- I would not enable drive API for this, I mean what is the benefit
- I would use a free deployment, because the department would not release funds for a server which is not needed after 15-30 days. not gonna use GCP/Azure/AWS for this and use up my credits.

2. I would download the MPR data, do fixes like name fixing etc manually, and save to the required data to whereever is needed.

3. I would create a sheet/excel workbook/config file containing Central Share: State Share ratio for each State/UT + Component (the actual format depends on what tech stack to use)

4. State Share Shortfall: It would be calculated as `Expected State Share Released based on ratio on CS:SS and Central Share Released in the MPR`

5. Since we are talking about funds, neither rounding off is to be tolerated nor +/-1 to be allowed

6. If Released(UC) >= Approved(UC), just flag it.

7. Post-upload validation is to be done

8. UX-wise, side by side preview pane for MPR and UC might be too much. We can have both columns in same preview table.

9. There are only two Roles: Consultans (who can download and upload) and Admin. Total Number of users: 14 consultants + 2 admins

10. Audit trail would be preferred if tech stack allows.

11. Once the pipeline works, we can worry about compliance or security needs (which I do not think is needed for an internal one time tool)

12. The excel sheet (or google sheet) containing the verified rows on successful verification should be timestamped versioned for easier roll back, and the rows themselves to have a timestamp column.

13. The entire excel file for MPR for All projects (RUSA and PM_USHA combined) is at most 4000, so data manipulation can be done in memory.

---

For released(uc) == approved(uc), there is no need for flag, only flag to be raised for the validations i gave. The ratios does not change. so a hardcoded config.py migt be better.

There would be two excel files: 
- uploaded data with timestamp, and 
- successfully verified with timestamp

Validation to save to successfully verified would be all or nothing. either the uploaded projects are all verified or none

----

For now I intend to only create service functions which I would run via command line. 

I would add interfaces later (flask or streamlit depends)

---
There are two different MPR.

`RUSA MPR` having RUSA Phase values: RUSA 1 and RUSA 2
with following columns
- S.No
- State
- District
- Months
- Year
- Component Name
- RUSA Phase
- Institution Name
- Aishe Code
- PAB Meeting Number
- PAB Date
- Central Share Approved

- Central Share Released

- Central Share Utilised

- State Share Approved

- State Share Released
- State Share Utilised
- Total Amount Approved
- Total Amount Released
- Total Amount Utilised
- Activities that have been already undertaken in Current Month
- Activities that have been undertaken till Previous Month
- Activities yet to be undertaken
- Percentage Physical Progress Total
- Whether PM Digitally Launched Project (Yes/ No)
- Project Inauguration status [Inaugurated/ Not Inaugurated]
- If Inaugurated, then, by whom and when
- Tentative Date of completion
- Project Status
- Whether the project is Functional[ or Lying idle/Not Functional]*
- If the Project is completed but not functional, Please state the reason(s):
- Benfits from the projects (Please provide details)
- Number of students benefitted
- Number of faculties benefitted
- Number of research works being undertaken
- Physical Inspection Reports (PIR)
- PIR Uploaded (Yes/No/Not Selected)

and 
`PM-USHA MPR` corresponding to projects with RUSA Phase `PM-USHA` with following columns
S.No
State
District
Component Name
RUSA Phase
Institution Name
Aishe Code
PAB Meeting Number
PAB Date
Central Share Amount Approved
Central Share Amount Released
Central Share Amount Utilised
State Share Amount Approved
State Share Amount Released
State Share Amount Utilised
Total Amount Approved
Total Amount Released
Total Amount Utilised
Physical Progress (Overall Project)(%)
Project Status (Overall)
Monthly Proposal Item Status (Completed)
Monthly Proposal Item Status (Ongoing)
Monthly Proposal Item Status (Not yet started)
Total Monthly Proposal Item Status
Is Focus District
Is Aspirational District
Is Left Wing Extremist (LWE) District
Is Border Area District
NAAC Accreditation Status
Accreditation Score
Accreditation Grade
Accreditation Valid Until
Year
Month

The end user flow would allow user to select 
- one or more rusa phases : rusa 1, rusa 2, and/or pm-usha, and 
- select one or more states/UTs, and
- generate the template

However, as you can see, the cols and name are slightly different in the two excel files.

Therefore, the mpr loader would first need to load the two excel as separate dfs, do state name canonical process on both dfs, then ensure that the required columns in both dfs are similar so that pd.concat can happen, then combine dfs to single df

---

Since we have the core logic (Verification Engine and Template Generator) and the roadmap finalized, we can now move into the **Integration Phase**. This sprint plan focuses on building the Flask "scaffolding"—the structure that holds the database, the user roles, and the service routes together.

---

### **Sprint 5: Core Scaffolding & Integration**

**Goal**: Establish the Flask environment, define the SQLite/SQLAlchemy models, and implement the "Gatekeeper" logic to prevent duplicate validations.

#### **Phase 1: Environment & Extension Setup**
*   **App Factory Pattern**: Initialize the Flask application using `create_app()` to handle extensions (SQLAlchemy, Flask-Login, Migrate) and Blueprints cleanly.
*   **Directory Mapping**: Create a startup utility to ensure `data/master`, `data/temp`, `data/verified`, and `data/review` exist on the PythonAnywhere file system.
*   **Database Config**: Configure the `SQLALCHEMY_DATABASE_URI` for a local `.db` file and initialize the engine.

#### **Phase 2: User Management & CLI**
*   **User Model Implementation**: Create the model with `username`, `password_hash`, `role`, and the optional fields (`email`, `first_name`, `last_name`).
*   **RBAC Decorators**: Build custom Python decorators (e.g., `@admin_required`) to protect specific routes like "Global Export."
*   **Flask CLI Commands**: Develop custom terminal commands:
    *   `flask init-db`: Creates tables and default folders.
    *   `flask create-user`: A prompted utility to add consultants or IT managers without SQL.

#### **Phase 3: The "Gatekeeper" Blueprint (Verifier Integration)**
*   **Route Logic**: Create the `/upload` route that accepts the consultant's file.
*   **Duplicate Detection**: Before calling the service, query the `ValidationLog` table for a `Success` status matching the file's `State` and `Phase`.
*   **Service Integration**:
    *   If no duplicate exists, pass the file to the `VerificationEngine`.
    *   On success, write to the `ValidationLog` and append the results to the `VerifiedRecords` table.
    *   On failure, serve the **Locked Discrepancy Annexure**[cite: 1].

#### **Phase 4: Template & Global Export Blueprints**
*   **Template Route**: Integrate `generate_consultant_template` into a route that serves the file as a `BytesIO` object or a direct download.
*   **The "IT Manager" Export**: Create the admin-only route that queries `VerifiedRecords`, converts it to a DataFrame, and exports the **Global Master** spreadsheet.

---

### **Deliverables Checklist**
| Component | Function |
| :--- | :--- |
| **`models.py`** | SQLite schema for Users, Logs, and Global Records. |
| **`commands.py`** | CLI tools for user management and DB setup. |
| **`auth` Blueprint** | Login/Logout and session protection. |
| **`verifier` Blueprint** | Upload handling, duplicate checking, and database "Commit" logic. |


For gatekeeper flow, I was thinking of doing this:

first a base.html using bootstrap 5.3 and js
a home page

then two tabs:
1. Generate Template
2. Verify UC details

For generate template:
1. User would select state and RUSA Phase (each is optional)
2. Click on generate template
3. On successful generate, download template button appears
4. On Failed generate, contact to admin appears

For Verify UC details
1. File Upload option that only accepts .xlsx file. Use extension and magic number based validation
2. On upload, Proceed to verify button appears.
3. On process and error page, a preview page comes showing the rows with problems. preview page would be tabular and paginated (frontend based because data is not too heavy). And button to download discrepancy .xlsx. and ValidationLog model is updated with new entry failure status. and a button to go back to upload page
4. On process and succes, a preview page comes showing that all data are correct. Preview page would be tabular and paginated (frontend based because data is not too heavy). And a button to submit verified data
5. On submit click, update the VerificationRecord with latest entries. and ValidationLog model is updated with a new entry with success status.

I am thinking of globally keeping the mpr_data in memory. 
Since the MPR file is small, we can simply load it on server start. that way we would avoid any race conditions from multi user sessions

Let us discuss this flow in detail and how UX, process and control flow would work. no code

---

yes, I like to define the structure of the "Success/Failure" preview table so we can ensure the frontend pagination handles the discrepancy flags correctly

For sake of UX and business use case, I would like to have following columns:

State
RUSA Phase
Component Name
District
Institution Name
PAB No
PAB Meeting Date
MPR Total Amount Approved : refers to the data from the master dataframe
MPR Total Amount Released : refers to the data from the master dataframe
MPR Total Amount Utilised : refers to the data from the master dataframe
MPR Central Share Approved : refers to the data from the master dataframe
MPR Central Share Released : refers to the data from the master dataframe
MPR Central Share Utilised : refers to the data from the master dataframe
MPR State Share Approved : refers to the data from the master dataframe
MPR State Share Released : refers to the data from the master dataframe
MPR State Share Utilised : refers to the data from the master dataframe
UC Total Amount Approved : refers to the entry made in the uploaded excel file
UC Total Amount Released : refers to the entry made in the uploaded excel file
UC Total Amount Utilised : refers to the entry made in the uploaded excel file
UC Central Share Approved : refers to the entry made in the uploaded excel file
UC Central Share Released : refers to the entry made in the uploaded excel file
UC Central Share Utilised : refers to the entry made in the uploaded excel file
UC State Share Approved : refers to the entry made in the uploaded excel file
UC State Share Released : refers to the entry made in the uploaded excel file
UC State Share Utilised : refers to the entry made in the uploaded excel file
- Optional Column in Case of error: Discrepancy Detail: contain the new line separated values of errors. For example, the errors from verification engine are in this format: `Shortfall Detected: State released 30000000.0, but based on Central release of 60000000.0, the State owed 40000000.0. Shortfall Amount: 10000000.0 | Flow Error: Total Utilized (99997693.0) &gt; Released (90000000.0).`, then split on the pipe character, and show in separate lines.

I see no use of showing project_id_key to user as it is an internal piece of logic.
Also, for the rows where the errors are, make bg slightly red.

On preview page show counts: Successfully verified rows, Rows with discrepancy. And a checkbox mentioning: `Only show the rows with discrepancies`, this would shorten the table and only show discrepant rows. 
As you can see from the uploaded mpr_loader, template_generator, verification engine and main.py I created for testing the cli based logics, you can see that most of the work is already done. In the next message, I would share the flask codes I have written.
Do you understand what this means? No code. revise the flow