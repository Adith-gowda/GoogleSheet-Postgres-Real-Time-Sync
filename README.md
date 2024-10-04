# Google Sheets - PostgreSQL Real-Time Sync Solution

## Overview
This project demonstrates a solution for real-time synchronization of data between Google Sheets and a PostgreSQL database using Flask as a middleware. The goal is to keep both the Google Sheet and the database in sync during CRUD operations, reflecting changes immediately on either platform.

## Tech Stack Used
1. **Google Sheets API**: Accessed using a service account created in Google Cloud Platform (GCP).
2. **Google Sheets Apps Script**: Utilized to create triggers for syncing data changes in Google Sheets to the PostgreSQL database.
3. **Flask App**: Acts as a server to handle requests from Google Sheets and manage CRUD operations on the PostgreSQL database.
4. **PostgreSQL Database**: The database where data is stored and synchronized.
5. **Ngrok**: Provides a public URL for the Flask server to allow communication with Google Sheets Apps Script functions.

## Workflow / Planned Approach
1. **Understanding the Problem**:
   - First, I created a service account in GCP and obtained the Google Sheets API credentials.
   
2. **Real-Time Synchronization Approach**:
   - The key to real-time synchronization is to use event-driven triggers. Apps Script in Google Sheets provides triggers that can call a function when the sheet's content changes.
   
3. **Apps Script Integration**:
   - I wrote functions in Apps Script that are triggered on changes in Google Sheets. These functions call the Flask server's Ngrok URL with the updated data.
   - Apps Script must be deployed as a Web App to generate a deployment URL that can be used in the code. The editor for Apps Script can be found under `Extensions` in Google Sheets.

4. **Flask as Middleware**:
   - The Flask app, running locally, receives data from the Google Sheets Apps Script via the Ngrok public URL. It then updates the PostgreSQL database using SQLAlchemy ORM.
   - Ngrok maps requests from the public URL to the local Flask app, enabling communication between Google Sheets and the local server.

5. **Database Triggers**:
   - PostgreSQL database triggers and listeners detect changes in the database. On detecting changes, they notify the Flask server, which then sends the update to Google Sheets using the Web App URL from Apps Script.

## Code Structure and Implementation

### `code.gs` (Google Apps Script)
This script is hosted in Google Sheets and listens for changes in the spreadsheet. It sends HTTP requests to the Flask app when data is updated, deleted, or inserted.

**Key Functions:**
- `initializeIDs()`: Initializes a list of IDs currently in the sheet.
- `syncRowToServer(e)`: Sends row data to the Flask server on edit.
- `deleteRowFromServer(rowID)`: Deletes a row from the server.
- `onChange(e)`: Detects changes in the sheet and triggers synchronization.
- `atEdit(e)`: Triggers `syncRowToServer` on edit.
- `doPost(e)`: Handles incoming requests to update the sheet.

### `server.py` (Flask App)
This is the main backend application that handles synchronization between Google Sheets and the PostgreSQL database.

**Key Routes:**
- `/sync_from_sheet` (POST): Receives and syncs data from Google Sheets to PostgreSQL.
- `/delete_row` (DELETE): Deletes a row in the database based on the ID provided by Google Sheets.
- `listen_for_changes()`: Listens for changes in the PostgreSQL database and triggers updates to Google Sheets using the Web App URL.

### `sync_script.py`
This script contains functions for syncing data between Google Sheets and PostgreSQL manually.

**Key Functions:**
- `sync_sheet_to_db()`: Syncs data from Google Sheets to the PostgreSQL database.
- `sync_db_to_sheet()`: Syncs data from the PostgreSQL database to Google Sheets.

## Instructions

### Setting Up the Project
1. **Google Cloud Platform**:
   - Create a project and enable the Google Sheets and Google Drive APIs.
   - Generate a service account and download the JSON key file. This file should be placed in the project directory.

2. **Google Sheets Apps Script**:
   - Open Google Sheets, go to `Extensions` > `Apps Script`.
   - Paste the contents of `code.gs` into the editor.
   - Deploy the script as a Web App and note the URL.

3. **Flask Application**:
   - Install dependencies using `pip install -r requirements.txt`.
   - Update the `SHEETS_WEBHOOK_URL` in `server.py` with the Web App URL from the Apps Script deployment.
   - Run the Flask server using `python server.py`.

4. **Ngrok Setup**:
   - Start Ngrok with `ngrok http 5000` and update the `SYNC_URL` and `DELETE_URL` in `code.gs` with the generated public URL.

5. **PostgreSQL Database**:
   - Set up a local PostgreSQL database and create a table `data_sync` as described in `server.py`.
   - Update the database credentials in `server.py` and `sync_script.py`.

6. **Updating Links**:
   - **Ngrok URL**: The Ngrok link is temporary and changes with each session. Update `SYNC_URL` and `DELETE_URL` in `code.gs` every time the Ngrok URL changes.
   - **Google Apps Script Deployment URL**: Update the `SHEETS_WEBHOOK_URL` in `server.py` with your own deployment URL.

## Notes
- Make sure to replace my service account JSON file with your own credentials in `sync_script.py`.
- Update the Ngrok link and Apps Script Web App URL whenever required.
- This solution supports syncing Google Sheets with a local PostgreSQL database. For cloud databases, update the connection parameters accordingly.

## Contact
For any queries, please contact [adithgowda06@gmail.com]