# API to Database Sync

A Python project that synchronizes data from an **external API** to a **PostgreSQL database** with automatic history tracking.

## Project Overview

This project:
- ✅ Fetches data from external API incrementally
- ✅ Flattens and transforms nested JSON data into tabular format
- ✅ Syncs data to PostgreSQL using efficient COPY operations
- ✅ Automatically adds new columns when API schema changes
- ✅ Maintains sync history in Excel log file for easy auditing
- ✅ Resumes from last sync point on restart (no duplicate data)

## Project Structure

```
data-analyze-portfolio/
├── src/
│   └── api_data_sync.py        # Main sync script
├── logs/                        # Directory for log files
├── .env.example                # Environment variables template
├── .env                         # Local environment variables (git ignored)
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- API credentials (appid, token)

## Installation

### 1. Clone or Setup Project

```bash
cd data-analyze-portfolio
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the template file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# API Configuration
API_BASE_URL=https://api.example.com
API_ENDPOINT=data/sync
API_APPID=your_app_id
API_AUTH=5
API_TOKEN=your_api_token

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/data_sync_db

# Logging
LOG_FILE_PATH=sync_history_log.xlsx
```

### 5. Create Database

Ensure your PostgreSQL database exists:

```sql
CREATE DATABASE data_sync_db;
```

## Usage

### Run the Sync Script

```bash
python src/api_data_sync.py
```

The script will:
1. ✅ Check for existing sync history
2. ✅ Resume from last timestamp or start from beginning
3. ✅ Fetch data from API page by page
4. ✅ Flatten nested JSON into table format
5. ✅ Insert/update data in PostgreSQL
6. ✅ Update sync history log

### Example Output

```
ℹ️  No log file found: starting full sync from beginning

--- 🔄 Page 1 | TS: 0x0000000000000000 ---
📡 Fetching from API...
🚀 Syncing 1250 rows from 2024-05-01 to database...
✅ Sync successful! History updated.

--- 🔄 Page 2 | TS: 0x1234567890abcdef ---
🚀 Syncing 1180 rows from 2024-05-02 to database...
✅ Sync successful! History updated.

>>> 🎉 Data is up to date
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_BASE_URL` | API base URL | `https://api.example.com` |
| `API_ENDPOINT` | API endpoint path | `data/sync` |
| `API_APPID` | Your app ID | `your_app_id` |
| `API_AUTH` | Auth type | `5` |
| `API_TOKEN` | Your API token | `your_token_here` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `LOG_FILE_PATH` | Path to sync history file | `sync_history_log.xlsx` |

## Data Schema

The script automatically creates the `sales_transactions` table with the following column structure:

### Sale-Level Columns
- `sale.id` - Transaction ID
- `sale.businessDateTime` - Transaction timestamp
- `sale.amount` - Transaction amount
- `sale.status` - Transaction status
- ... (and other sale fields)

### Item-Level Columns
- `items.id` - Item ID
- `items.name` - Product name
- `items.quantity` - Quantity
- `items.price` - Unit price
- `items.priceSchemes.*` - Price scheme details

### Collection-Level Columns
- `collection.id` - Collection ID
- `collection.name` - Collection name
- ... (and other collection fields)

## Features

### ✅ Incremental Sync
- Resumes from last sync timestamp
- No duplicate data transfers
- Efficient page-by-page processing

### ✅ Schema Flexibility
- Automatically adds new columns when API schema changes
- No need to manually alter table structure

### ✅ Data Transformation
- Flattens nested JSON into tabular format
- Proper column naming with prefixes (sale., items., collection.)
- One row per item (from items array)

### ✅ Performance
- Uses PostgreSQL COPY command for bulk insert
- Efficient data streaming with pandas
- Network timeout handling and retry logic

### ✅ Audit Trail
- Excel log file tracks all syncs
- Records timestamp, business date, row count, sync time
- Easy to audit data quality and sync history

## Troubleshooting

### Connection Error to Database
```
❌ Error: could not connect to server: Connection refused
```
**Solution:** Ensure PostgreSQL is running and credentials in `.env` are correct.

### API Authentication Failed
```
❌ API Error: 401
```
**Solution:** Check API credentials (appid, token) in `.env` file.

### Network Timeout
```
📡 Network Error: timeout
```
**Solution:** Script automatically retries after 10 seconds. Check your internet connection.

### Environment Variables Not Loading
```
ValueError: DATABASE_URL environment variable is not set!
```
**Solution:** Ensure `.env` file exists and `.env` is in the project root directory.

## Security Best Practices

⚠️ **IMPORTANT:** Never commit `.env` file to Git!

The `.gitignore` file already excludes it, but make sure:
- ✅ Use `.env.example` as template with placeholder values
- ✅ Add real credentials only to local `.env` file
- ✅ Never share `.env` file with others
- ✅ Use environment-specific `.env` files for different environments

## License

This project is part of the data analysis portfolio.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review environment variables in `.env`
3. Check PostgreSQL connection
4. Review API status and credentials
