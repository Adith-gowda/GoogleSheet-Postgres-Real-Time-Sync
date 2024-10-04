

# This script listens for notifications from a PostgreSQL database and sends the data to a Google Sheets webhook.
# This script is mainly used for testing purpose and should be run in a separate terminal. But its integrated in the server.py file as well.


import psycopg2
import select
import json
import requests
from threading import Thread

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
        print(f"Error sending data to Google Sheets: {str(e)}")

if __name__ == "__main__":
    listener_thread = Thread(target=listen_for_changes)
    listener_thread.start()
