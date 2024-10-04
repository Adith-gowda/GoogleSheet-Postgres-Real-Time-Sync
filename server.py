from flask import Flask, request, jsonify
import psycopg2
import select
import requests
from threading import Thread
import json
from sync_script import sync_db_to_sheet

app = Flask(__name__)

# This is my personal user account in Postgres, named "postges" with password "123456789"

#Asumming that you have already created a database named "sync_db" in your PostgreSQL server
#Asumming that you have already created a table named "data_sync" in your "sync_db" database
#Asumming that you have already created a table with the following schema:
#CREATE TABLE data_sync (
#    id VARCHAR(255) PRIMARY KEY,
#    name VARCHAR(255),
#    age INTEGER,
#    email VARCHAR(255)
#);

# Function to establish a connection to the PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="sync_db",
        user="postgres",
        password="123456789"
    )
    return conn

# Flask route for syncing from Google Sheets to PostgreSQL
@app.route('/sync_from_sheet', methods=['POST'])
def sync_from_sheet():
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    cursor = None
    conn = None
    try:
        row_id = data.get('ID')
        if row_id == '':
            print("No ID provided, Please provide ID")
            return jsonify({'status': 'error', 'message': 'No ID provided'}), 400
        name = data.get('Name', '').strip() or None  
        age = data.get('Age') if data.get('Age') != '' else None  
        email = data.get('Email', '').strip() or None  

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the row exists
        cursor.execute("SELECT id FROM data_sync WHERE id = %s;", (row_id,))
        existing_row = cursor.fetchone()

        if existing_row:  
            cursor.execute("""
                UPDATE data_sync 
                SET name = %s, age = %s, email = %s
                WHERE id = %s;
            """, (name, age, email, row_id))
        else:  
            cursor.execute("""
                INSERT INTO data_sync (id, name, age, email) 
                VALUES (%s, %s, %s, %s);
            """, (row_id, name, age, email))

        conn.commit()  
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# Flask route for handling row deletion
@app.route('/delete_row', methods=['DELETE'])
def delete_row():
    row_id = request.args.get('ID')
    if not row_id:
        return jsonify({'status': 'error', 'message': 'No ID provided'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM data_sync WHERE id = %s;", (row_id,))
        conn.commit()  

        return jsonify({'status': 'success', 'message': 'Row deleted'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Webhook configuration - This link corresponds to the Google Apps Script version 2 deployment Web App URL.
# This URL is generated when you deploy the Google Apps Script as a Web App.
# You can find this URL by going to the Google Apps Script project and clicking on "Deploy" > "New Deployment" > "Web App".
# Copy the "Current web app URL" and paste it here. Make sure to append "/exec" at the end of the URL.
# In my case its version 2 of deployment URL

# For reference I will attach the URL or access to the Google Sheets with public access in the README.md file
SHEETS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxdJtJJ6Vrye8E3UfKAkH9gI7PSdL8Aa38kcPo1dmvd-4axTO-8mgLg5ZcZzldA2nwC-A/exec"

def listen_for_changes():
    conn = psycopg2.connect(
        host="localhost",
        database="sync_db",
        user="postgres",
        password="123456789"
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute("LISTEN data_changes;")
    print("Listening for data changes...")

    while True:
        if select.select([conn], [], [], 5) == ([], [], []):
            # Timeout occurred, no events
            continue
        else:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                payload = json.loads(notify.payload)
                print(f"Received notification: {payload}")
                send_webhook(payload)

def send_webhook(data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            SHEETS_WEBHOOK_URL,
            json=data,
            headers=headers
        )
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get('status') == 'success':
                print("Data sent to Google Sheets successfully.")
            else:
                print(f"Failed to send data: {response_json.get('message')}")
        else:
            print(f"Failed to send data to Google Sheets. Status Code: {response.status_code}")
    except Exception as e:
        print(f"processing...: {str(e)}")


# Main function to run the Flask app
if __name__ == '__main__':
    sync_db_to_sheet()
    
    listener_thread = Thread(target=listen_for_changes)
    listener_thread.start()

    app.run(port=5000)
