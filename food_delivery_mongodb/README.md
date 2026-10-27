# Online Food Delivery Analysis Using MongoDB for Big Data Processing

> **Academic Mini-Project** | Third-Year Computer Science Engineering  
> **Technology Stack:** Python · MongoDB · Streamlit · Plotly · Pandas

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Installation & Setup](#installation--setup)
6. [Importing Data](#importing-data)
7. [Running the Dashboard](#running-the-dashboard)
8. [Running Tests](#running-tests)
9. [Dashboard Pages](#dashboard-pages)
10. [CSV Column Reference](#csv-column-reference)
11. [MongoDB Collections](#mongodb-collections)
12. [Aggregation Pipeline Examples](#aggregation-pipeline-examples)
13. [Troubleshooting](#troubleshooting)
14. [Replacing Sample Data](#replacing-sample-data)

---

## Project Overview

This project demonstrates large-scale food delivery data analysis using MongoDB as the primary database and Streamlit as the interactive dashboard framework. All analytical computations (revenue aggregation, customer behaviour analysis, delivery performance metrics, etc.) are performed inside MongoDB using native aggregation pipelines, ensuring scalability beyond what a purely in-memory approach can offer.

**Problem Statement:** Online food delivery platforms generate millions of order records. Extracting actionable business intelligence from such datasets requires efficient storage, query optimisation, and interactive visualisation.

**Proposed Solution:** A modular Python application that ingests raw CSV data, cleanses and validates every record, stores it in MongoDB with appropriate indexes, and exposes an interactive Streamlit dashboard with six analytical pages.

---

## Features

| Module | Capability |
|--------|-----------|
| **Data Import** | Chunk-based CSV ingestion, validation, deduplication, import logs |
| **Overview** | KPI cards, monthly revenue trend, status/payment donuts, city bars |
| **Sales Analysis** | Daily/weekly/monthly revenue, category revenue, top restaurants |
| **Customer Analysis** | Order heatmap, hourly patterns, rating distribution, payment methods |
| **Restaurant Performance** | Top-10 tables, delivery time, ratings, cancellation rate |
| **Delivery Analysis** | Delivery-time distribution, city comparison, order status breakdown |
| **Data Explorer** | Paginated search, CSV export, file upload import, import history |
| **Advanced Analytics** | RFM customer segmentation, repeat-customer loyalty, discount impact |

---

## Project Structure

```
food_delivery_mongodb/
├── app.py                    # Streamlit entry-point & home page
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── generate_sample_data.py   # Generate synthetic test data
├── config/
│   └── settings.py           # Environment-based configuration
├── database/
│   ├── connection.py         # MongoDB singleton connection
│   ├── indexes.py            # Index creation & management
│   └── repositories.py       # CRUD & bulk upsert helpers
├── ingestion/
│   ├── import_data.py        # CLI & programmatic CSV importer
│   ├── preprocessing.py      # Column normalisation & cleaning
│   └── validation.py         # Row-level validation rules
├── analytics/
│   ├── aggregations.py       # Core MongoDB aggregation pipelines
│   ├── advanced.py           # RFM segmentation, loyalty & discount analysis
│   ├── metrics.py            # High-level metric helpers
│   └── queries.py            # Paginated query & filter helpers
├── pages/
│   ├── 1_Overview.py
│   ├── 2_Sales_Analysis.py
│   ├── 3_Customer_Analysis.py
│   ├── 4_Restaurant_Performance.py
│   ├── 5_Delivery_Analysis.py
│   ├── 6_Data_Explorer.py
│   └── 7_Advanced_Analytics.py
├── utils/
│   ├── charts.py             # Plotly chart factory functions
│   ├── export.py             # CSV export helpers
│   └── helpers.py            # Streamlit UI helpers & KPI cards
├── data/
│   └── food_delivery_sample.csv
└── tests/
    ├── test_validation.py
    ├── test_metrics.py
    ├── test_aggregations.py
    └── test_advanced.py
```

---

## Prerequisites

- **Python 3.10+** (tested on 3.12/3.13)
- **MongoDB Community Server 7.x** *or* a MongoDB Atlas free cluster
- **Git** (optional, for version control)

---

## Installation & Setup

### 1. Open a terminal in the project folder

```powershell
cd "BDA p1\food_delivery_mongodb"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start MongoDB locally

**Option A — Local MongoDB:**
```powershell
# Ensure mongod is in PATH. Create the data directory first if needed:
mkdir C:\data\db
mongod --dbpath C:\data\db
```

**Option B — MongoDB Atlas (cloud):**
- Create a free cluster at [cloud.mongodb.com](https://cloud.mongodb.com)
- Copy your connection string

### 5. Configure environment

```powershell
copy .env.example .env
# Open .env and set MONGO_URI to your connection string
```

Example `.env`:
```
MONGO_URI=mongodb://localhost:27017/
DB_NAME=food_delivery_analytics
CHUNK_SIZE=1000
```

---

## Importing Data

### Import the sample dataset (1,000 synthetic orders)

```powershell
python -m ingestion.import_data data/food_delivery_sample.csv
```

### Create database indexes

```powershell
python -m database.indexes
```

### Expected output

```
── Import Summary ──────────────────────────────
  total_rows             : 1000
  inserted               : 1000
  updated                : 0
  rejected               : 0
  skipped                : 0
  errors                 : 0
  duration_seconds       : 1.23
────────────────────────────────────────────────
```

### Import a larger dataset

```powershell
python -m ingestion.import_data data/your_large_dataset.csv --chunk-size 2000
```

---

## Running the Dashboard

```powershell
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Running Tests

```powershell
pytest -q
```

To run a specific test file:
```powershell
pytest tests/test_validation.py -v
```

Tests use mocked database calls where possible and do **not** require a live MongoDB connection.

---

## Dashboard Pages

| Page | URL Route | Description |
|------|-----------|-------------|
| 🏠 Home | `/` | Project overview and quick-start guide |
| 📊 Overview | `/Overview` | KPI cards, trends, city comparison |
| 💰 Sales Analysis | `/Sales_Analysis` | Revenue trends, category & restaurant breakdown |
| 👥 Customer Analysis | `/Customer_Analysis` | Heatmap, ordering patterns, ratings |
| 🏪 Restaurant Performance | `/Restaurant_Performance` | Top restaurants, delivery, cancellations |
| 🚚 Delivery Analysis | `/Delivery_Analysis` | Delivery time distribution, city comparison |
| 🔍 Data Explorer | `/Data_Explorer` | Search, paginate, export, import |
| 🧠 Advanced Analytics | `/Advanced_Analytics` | RFM segmentation, loyalty analysis, discount impact |

---

## CSV Column Reference

| CSV Column | Internal Field | Required | Notes |
|-----------|----------------|----------|-------|
| `order_id` | `order_id` | ✅ Yes | Unique identifier |
| `order_date` | `order_date` | ✅ Yes | Any parseable date format |
| `restaurant_name` | `restaurant_name` | ✅ Yes | |
| `total_amount` | `total_amount` | ✅ Yes | Non-negative number |
| `customer_id` | `customer_id` | No | For repeat-customer analysis |
| `restaurant_id` | `restaurant_id` | No | |
| `city` | `city` | No | Used in city filters |
| `food_category` | `food_category` | No | |
| `item_name` | `item_name` | No | |
| `quantity` | `quantity` | No | Must be > 0 if present |
| `item_price` | `item_price` | No | Must be ≥ 0 if present |
| `discount` | `discount` | No | Defaults to 0 if absent |
| `delivery_fee` | `delivery_fee` | No | Defaults to 0 if absent |
| `payment_method` | `payment_method` | No | |
| `order_status` | `order_status` | No | Completed/Delivered/Cancelled/Pending |
| `delivery_time_minutes` | `delivery_time_minutes` | No | 0–600 range |
| `customer_rating` | `customer_rating` | No | 0–5 range |

Many alternative column name aliases are supported (e.g. `date` for `order_date`, `total` for `total_amount`). See `config/settings.py` for the full mapping.

---

## MongoDB Collections

### `orders`
Main collection with all order documents. Indexed on `order_id` (unique), `order_date`, `city`, `restaurant_name`, `food_category`, `order_status`, `payment_method`.

### `import_logs`
Records each import operation with timestamp, filename, counts (inserted/updated/rejected), and error messages.

---

## Aggregation Pipeline Examples

### Monthly Revenue (Completed Orders)
```javascript
db.orders.aggregate([
  { $match: { order_status: { $in: ["Completed", "Delivered"] } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m", date: "$order_date" } },
      revenue: { $sum: "$total_amount" },
      orders: { $sum: 1 }
  }},
  { $sort: { _id: 1 } }
])
```

### Top 10 Restaurants by Revenue
```javascript
db.orders.aggregate([
  { $match: { order_status: { $in: ["Completed", "Delivered"] } } },
  { $group: {
      _id: "$restaurant_name",
      revenue: { $sum: "$total_amount" },
      orders: { $sum: 1 }
  }},
  { $sort: { revenue: -1 } },
  { $limit: 10 }
])
```

### Order Activity Heatmap (Day × Hour)
```javascript
db.orders.aggregate([
  { $group: {
      _id: { day: { $dayOfWeek: "$order_date" }, hour: { $hour: "$order_date" } },
      orders: { $sum: 1 }
  }}
])
```

---

## Troubleshooting

| Error | Solution |
|-------|---------|
| `ConnectionError: Unable to connect to MongoDB` | Start `mongod` or verify Atlas URI in `.env` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` with venv active |
| `FileNotFoundError: .env` | Copy `.env.example` to `.env` |
| `duplicate key error` on import | Normal — duplicate `order_id` records are silently skipped |
| Charts show empty | Import data first via the Data Explorer or CLI |
| Streamlit port busy | Use `streamlit run app.py --server.port 8502` |

---

## Replacing Sample Data

1. Prepare your CSV with the columns listed above (or use supported aliases).
2. Place the file in the `data/` folder.
3. Run:
   ```powershell
   python -m ingestion.import_data data/your_file.csv --chunk-size 2000
   ```
4. Streamlit caches reset automatically every 2 minutes, or click **Clear Cache** in the ⋮ menu.

> **Note:** The sample dataset contains 1,000 synthetic records labelled as illustrative data. They should not be presented as real business findings.

---

## Performance Notes

- **Batch inserts** use `bulk_write` with `UpdateOne + upsert` for deduplication.
- **Aggregation pipelines** run entirely in MongoDB; Python only receives the summarised result.
- **Streamlit `@st.cache_data`** caches read-only results for 2 minutes (TTL=120s).
- **Indexes** are created on all frequently-filtered fields to avoid collection scans.
- MongoDB can scale to millions of records with appropriate hardware and index design; actual performance depends on your deployment.

---

*Generated as part of a third-year B.E. Computer Science mini-project demonstrating Big Data processing with MongoDB.*
