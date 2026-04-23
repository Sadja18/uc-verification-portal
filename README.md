# UC Verification Exercise

## Background:

- Projects are approved for given State/UT and Institution under RUSA and PM-USHA during various Project Approval Board Mettings (PAB Meeting).
- The implementing agency fills Monthyl Progress Report (MPR) for given project; combination of State/UT + Component Name + Institution Name + PAB meeting number
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