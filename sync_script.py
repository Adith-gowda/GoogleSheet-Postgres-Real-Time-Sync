import gspread
from oauth2client.service_account import ServiceAccountCredentials
import psycopg2
import pandas as pd

scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
# The JSON file is the key that allows you to authenticate with Google Sheets
# This is my JSON file, you need to replace it with your own JSON file if needed as it is my service account from google cloud platform
credentials = ServiceAccountCredentials.from_json_keyfile_name('semiotic-karma-436815-h2-c080065ca21f.json', scope)
client = gspread.authorize(credentials)

# This is a key from my Google sheet URL, You can find this between the "/d/" and "/edit" in the Google Sheet URL
spreadsheet_id = '1nXdcYBI3xW8B7wgxZj3YB8TC8l3WTj3XymMdcLxSe-c'
sheet = client.open_by_key(spreadsheet_id).sheet1

# Function to sync Google Sheet to PostgreSQL
def sync_sheet_to_db():
    connection = psycopg2.connect(
        dbname="sync_db",
        user="postgres",
        password="123456789",
        host="localhost",
        port="5432"
    )
    cursor = connection.cursor()
    
    sheet_data = sheet.get_all_records()
    df = pd.DataFrame(sheet_data)

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO data_sync (id, name, age, email)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) 
            DO UPDATE SET name = EXCLUDED.name, age = EXCLUDED.age, email = EXCLUDED.email;
        """, (row['id'], row['name'], row['age'], row['email']))
    
    # Commit changes
    connection.commit()
    print("Data synced from Google Sheet to PostgreSQL.")

    cursor.close()
    connection.close()

# Function to sync PostgreSQL to Google Sheet
def sync_db_to_sheet():
    connection = psycopg2.connect(
        dbname="sync_db",
        user="postgres", 
        password="123456789",
        host="localhost",
        port="5432"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM data_sync;")
    db_data = cursor.fetchall()

    sheet.clear()
    header = ['id', 'name', 'age', 'email']
    sheet.append_row(header)

    for row in db_data:
        sheet.append_row(list(row))
    
    print("Data synced from PostgreSQL to Google Sheet.")
    cursor.close()
    connection.close()
