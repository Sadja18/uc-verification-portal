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

