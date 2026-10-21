# CodexCode

PySide6 app for importing course journal Brightspace ZIP exports into per-course Excel workbooks.

## What works now

- Loads the course list from `CE_Course Journal Project.xlsx`.
- Uses a tabbed UI with `Importer`, `Grading`, and `Settings`.
- Lets you choose class, semester fallback, workbook, and assignment on the importer tab.
- Defaults each class workbook to the selected workbooks folder as `<class>workbook.xlsx`.
- Lets you change the workbooks folder in `Settings`, with the default still set to `./workbooks`.
- Provides an `Open Workbooks Folder` action in `Settings`.
- Accepts one or more Brightspace ZIP exports by drag and drop or file picker.
- Previews the number of detected `submission.txt` / `submission.html` responses.
- Detects semester per ZIP from the first submission entry date inside the archive.
- Supports importing ZIPs from different semesters into the same class in one batch.
- Uses workbook sheet names as the source of truth for ZIP-to-assignment matching.
- Creates missing course workbooks from the catalog when needed.
- Appends imported responses to the chosen workbook and worksheet.
- Preserves the example workbook layout:
  - metadata rows at the top
  - assignment name / text / rubric placeholder rows
  - response headers on row 19
  - imported responses starting on row 20
- Optionally writes import audit data to an `Advanced History` sheet when `Advanced metadata` is enabled in `Settings`.
- Supports both dark mode and light mode from `Settings`.

## Run

From this folder:

RUN_ME_TO_START.vbs

## Current workflow

1. Select the course.
2. Confirm or enter a semester fallback for ZIPs that do not expose a readable submission date.
3. Review the default workbook path for the selected class.
4. Select a default assignment.
5. Drop Brightspace ZIP files into the large import area.
6. Adjust the target assignment and semester for each ZIP if needed.
7. Import.

## Workbook conventions

- One workbook per course.
- One worksheet per assignment.
- Workbook sheet names are used for assignment recognition during ZIP import.
- `Advanced History` is reserved for optional import metadata logging and is not treated as an assignment sheet.

## Settings

- `Workbooks Folder`: where course workbooks are created and selected by default.
- `Open Workbooks Folder`: opens the current workbooks directory in the system file browser.
- `Semester Fallback`: used only when a ZIP does not contain a readable submission date for automatic semester detection.
- `Advanced metadata`: enables writing import audit rows to `Advanced History`.
- `Dark mode`: toggles between dark and light themes.

## Notes

The app is intentionally focused on importing and organizing submissions first.
The `Grading` tab is a placeholder for the later grading workflow.
AI grading, rubric generation, and D2L grade export should stay as later modules once the workbook structure is stable.
