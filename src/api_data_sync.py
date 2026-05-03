"""
API to Database Sync
Fetches data from an API and syncs to PostgreSQL database.
Maintains sync history in Excel log file.
"""
import requests
import pandas as pd
import time
import io
import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================== CONFIG ==================
BASE_URL = os.getenv("API_BASE_URL")
ENDPOINT = os.getenv("API_ENDPOINT")
LOG_FILE = os.getenv("LOG_FILE_PATH")

# API Headers
HEADERS = {
    "appid": os.getenv("API_APPID"),
    "auth": os.getenv("API_AUTH"),
    "token": os.getenv("API_TOKEN"),
    "Accept": "application/json"
}

# Database Configuration
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

engine = create_engine(DB_URL)


def get_start_timestamp():
    """
    Check if log file exists and get the latest timestamp from history.
    Returns the starting timestamp for API sync.
    """
    if os.path.exists(LOG_FILE):
        try:
            df_history = pd.read_excel(LOG_FILE)
            if not df_history.empty:
                start_ts = str(df_history.iloc[-1]['Timestamp'])
                print(f"🔄 Found sync history: resuming from TS {start_ts}")
                return start_ts
            else:
                print(f"⚠️  Log file is empty: starting fresh from beginning")
                return "0x0000000000000000"
        except Exception as e:
            print(f"❌ Failed to read log file: {e}. Starting fresh.")
            return "0x0000000000000000"
    else:
        print(f"ℹ️  No log file found: starting full sync from beginning")
        return "0x0000000000000000"


def fetch_api_data():
    """
    Fetch data from API and sync to PostgreSQL database.
    """
    current_ts = get_start_timestamp()
    page_count = 0

    while True:
        print(f"\n--- 🔄 Page {page_count + 1} | TS: {current_ts} ---")

        try:
            params = {"starttimestamp": current_ts}
            response = requests.get(
                f"{BASE_URL}/{ENDPOINT}",
                headers=HEADERS,
                params=params,
                timeout=180
            )
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                time.sleep(10)
                continue
        except Exception as e:
            print(f"📡 Network Error: {e}")
            time.sleep(10)
            continue

        res_json = response.json()
        data_sect = res_json.get("data", {})
        sales_list = data_sect.get("sales", [])
        next_ts = data_sect.get("lastTimestamp")

        if next_ts is None or next_ts == current_ts:
            print(">>> 🎉 Data is up to date")
            break

        if not sales_list:
            print(f"⏩ Skipping empty page to TS: {next_ts}")
            current_ts = next_ts
            continue

        # Process and flatten data
        all_rows = []

        for sale in sales_list:
            items = sale.get('items', [])
            collections = sale.get('collection', [])

            # Get first collection or empty dict
            collection_data = collections[0] if collections else {}

            # For each item in the sale, create a row
            for item in items:
                row = {}

                # Add sale-level fields with 'sale.' prefix
                for key, value in sale.items():
                    if key not in ['items', 'collection', 'voucher', 'extendedSales',
                                   'client', 'billingAddress', 'shippingAddress']:
                        row[f'sale.{key}'] = value

                # Add nested client fields
                if 'client' in sale and isinstance(sale['client'], dict):
                    for key, value in sale['client'].items():
                        if key not in ['billingAddress', 'shippingAddress']:
                            row[f'sale.client.{key}'] = value

                # Add item-level fields with 'items.' prefix
                for key, value in item.items():
                    if key != 'priceSchemes':
                        row[f'items.{key}'] = value

                # Add priceSchemes fields
                if 'priceSchemes' in item and isinstance(item['priceSchemes'], dict):
                    for key, value in item['priceSchemes'].items():
                        row[f'items.priceSchemes.{key}'] = value

                # Add collection fields with 'collection.' prefix (always index 0)
                for key, value in collection_data.items():
                    row[f'collection.{key}'] = value

                all_rows.append(row)

        df = pd.DataFrame(all_rows)

        # Extract business date for logging
        df['businessDate_only'] = pd.to_datetime(df['sale.businessDateTime']).dt.date
        sample_date = df['businessDate_only'].iloc[0] if not df.empty else "N/A"

        # Check if table exists
        inspector = inspect(engine)
        if not inspector.has_table("sales_transactions"):
            df.head(0).to_sql('sales_transactions', engine, if_exists='replace', index=False)

        # Add new columns if schema changes
        existing_cols = [col['name'] for col in inspector.get_columns("sales_transactions")]
        new_cols = set(df.columns) - set(existing_cols)

        if new_cols:
            with engine.begin() as conn:
                for col in new_cols:
                    conn.execute(text(f'ALTER TABLE sales_transactions ADD COLUMN "{col}" TEXT'))

        # Insert data using COPY for performance
        print(f"🚀 Syncing {len(df)} rows from {sample_date} to database...")
        try:
            output = io.StringIO()
            df.to_csv(output, sep='\t', header=False, index=False, na_rep='NULL')
            output.seek(0)

            connection = engine.raw_connection()
            cursor = connection.cursor()
            columns = [f'"{col}"' for col in df.columns]
            sql = f"COPY sales_transactions ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER '\t' NULL 'NULL'"
            cursor.copy_expert(sql=sql, file=output)
            connection.commit()
            cursor.close()
            connection.close()

            # Update log file with sync history
            new_log = pd.DataFrame([{
                'Timestamp': next_ts,
                'BusinessDate': str(sample_date),
                'Rows_Synced': len(df),
                'Sync_Time': time.strftime("%Y-%m-%d %H:%M:%S")
            }])

            if os.path.exists(LOG_FILE):
                df_history = pd.read_excel(LOG_FILE)
                df_history = pd.concat([df_history, new_log], ignore_index=True)
            else:
                df_history = new_log

            df_history.to_excel(LOG_FILE, index=False)
            print(f"✅ Sync successful! History updated.")

        except Exception as e:
            print(f"❌ Sync failed: {e}")
            break

        current_ts = next_ts
        page_count += 1
        time.sleep(0.1)


if __name__ == "__main__":
    fetch_api_data()
