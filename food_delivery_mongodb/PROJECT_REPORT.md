# Project Report: Online Food Delivery Analysis Using MongoDB for Big Data Processing

---

## Abstract

This project presents a comprehensive big data analytics application for the online food delivery domain, developed as a third-year Computer Science Engineering mini-project. The system ingests large volumes of food delivery order data from CSV files into MongoDB, an industry-standard NoSQL document database, and exposes an interactive multi-page dashboard built with Streamlit and Plotly. All analytical computations—including revenue aggregation, delivery performance metrics, customer ordering-behaviour analysis, and restaurant performance benchmarking—are performed inside MongoDB using native aggregation pipelines, rather than loading entire collections into application memory. The system demonstrates how modern NoSQL databases can address scalability, schema flexibility, and query performance requirements that arise in real-world food delivery platforms.

---

## 1. Introduction

The rapid growth of food delivery services such as Zomato, Swiggy, Uber Eats, and DoorDash has produced enormous volumes of transactional data. Each order generates multiple data points: customer identity, restaurant, food items, pricing, payment information, delivery time, and post-delivery ratings. When millions of such records accumulate over months or years, traditional relational databases can struggle to maintain query performance, while purely in-memory analytics tools cannot handle the data volume efficiently.

MongoDB, as a document-oriented database, offers horizontal scalability, flexible schema design, and powerful aggregation framework capabilities that make it well-suited for big data analytics workloads. Combined with Python for application logic, Streamlit for rapid dashboard development, and Plotly for interactive visualisations, the chosen technology stack delivers a maintainable, demonstrable analytics platform.

---

## 2. Problem Statement

Online food delivery businesses need to answer a range of analytical questions:

- Which restaurants generate the most revenue and which have the highest cancellation rates?
- What are the peak ordering hours and busiest weekdays?
- How does delivery performance vary across cities?
- Which food categories are most popular?
- What is the realized revenue after accounting for discounts and cancelled orders?

Answering these questions requires processing potentially millions of records efficiently, maintaining data quality through validation and deduplication, and presenting results in an accessible visual format for business stakeholders.

---

## 3. Objectives

1. Design and implement a MongoDB database schema optimised for food delivery analytics.
2. Develop a robust CSV ingestion pipeline with chunk-based processing, validation, and deduplication.
3. Implement efficient MongoDB aggregation pipelines for all required analytical queries.
4. Build a professional, interactive Streamlit dashboard with six analytical pages.
5. Provide CSV export capability, global filter controls, and pagination for large result sets.
6. Write automated tests for data cleaning, validation, and metric calculations.
7. Demonstrate that the system scales beyond the sample dataset.

---

## 4. Existing Systems and Their Limitations

Traditional approaches to food delivery analytics typically involve:

| Approach | Limitation |
|----------|-----------|
| Relational databases (MySQL/PostgreSQL) | Fixed schema; JOIN performance degrades on very large datasets; difficult to evolve schema |
| Flat-file analysis (Excel, CSV) | Not scalable; no concurrent access; no real-time updates |
| Pure Pandas in-memory analysis | Cannot handle datasets larger than available RAM; no persistence |
| Basic reporting tools | No real-time filtering; not connected to live databases |

**Proposed advantage:** MongoDB's aggregation framework processes data at the database layer, returning only aggregated results to the application, which dramatically reduces network transfer and memory consumption.

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER BROWSER                           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│              STREAMLIT DASHBOARD (app.py + pages/)          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Overview │ │  Sales   │ │Customer  │ │Restaurant│  ...  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                    utils/ (charts, helpers, export)         │
└──────────────────────────┬──────────────────────────────────┘
                           │ Python calls
┌──────────────────────────▼──────────────────────────────────┐
│              ANALYTICS LAYER (analytics/)                   │
│  aggregations.py · metrics.py · queries.py                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ PyMongo
┌──────────────────────────▼──────────────────────────────────┐
│              DATABASE LAYER (database/)                     │
│  connection.py · indexes.py · repositories.py               │
└──────────────────────────┬──────────────────────────────────┘
                           │ MongoDB Wire Protocol
┌──────────────────────────▼──────────────────────────────────┐
│              MONGODB (food_delivery_analytics)               │
│  collections: orders · import_logs                          │
└─────────────────────────────────────────────────────────────┘

         CSV Files ──▶ ingestion/ ──▶ MongoDB
```

---

## 6. Hardware and Software Requirements

### Minimum Hardware
- CPU: Dual-core 2.0 GHz
- RAM: 4 GB (8 GB recommended for large datasets)
- Storage: 5 GB free space
- Network: Required for MongoDB Atlas; optional for local deployment

### Software
| Component | Version |
|-----------|---------|
| Operating System | Windows 10/11, macOS, or Linux |
| Python | 3.10 or higher |
| MongoDB Community Server | 7.x |
| Streamlit | 1.32+ |
| PyMongo | 4.6+ |
| Pandas | 2.1+ |
| Plotly | 5.18+ |

---

## 7. MongoDB Database Design

### Database: `food_delivery_analytics`

### Collection: `orders`

```json
{
  "_id": ObjectId("..."),
  "order_id": "ORD000001",
  "order_date": ISODate("2024-03-15T14:32:00Z"),
  "customer_id": "CUST0042",
  "restaurant_id": "REST001",
  "restaurant_name": "Spice Garden",
  "city": "Mumbai",
  "food_category": "Indian",
  "item_name": "Butter Chicken",
  "quantity": 2,
  "item_price": 280.00,
  "discount": 56.00,
  "delivery_fee": 40.00,
  "total_amount": 544.00,
  "payment_method": "UPI",
  "order_status": "Completed",
  "delivery_time_minutes": 35,
  "customer_rating": 4.5
}
```

### Indexes on `orders`

| Index Name | Fields | Type | Purpose |
|-----------|--------|------|---------|
| `order_id_unique` | order_id | Unique | Deduplication |
| `order_date_desc` | order_date DESC | Single | Date-range queries |
| `city_asc` | city | Single | City filter |
| `restaurant_name_asc` | restaurant_name | Single | Restaurant filter |
| `food_category_asc` | food_category | Single | Category filter |
| `order_status_asc` | order_status | Single | Status filter |
| `payment_method_asc` | payment_method | Single | Payment filter |
| `date_status_compound` | (order_date DESC, order_status ASC) | Compound | Revenue aggregations |

### Collection: `import_logs`

```json
{
  "_id": ObjectId("..."),
  "filename": "food_delivery_sample.csv",
  "imported_at": ISODate("2024-10-24T18:05:00Z"),
  "total_rows": 1000,
  "inserted": 1000,
  "updated": 0,
  "rejected": 0,
  "skipped": 0,
  "errors": []
}
```

---

## 8. Data Processing Methodology

### Import Pipeline

```
CSV File
   │
   ▼
pd.read_csv() in chunks (default 1,000 rows)
   │
   ▼
preprocessing.clean_dataframe()
   ├── Normalise column names
   ├── Apply column mapping (aliases → canonical names)
   ├── Drop fully empty rows
   ├── Strip string whitespace
   ├── Parse order_date → datetime
   ├── Coerce numeric columns
   └── Fill optional missing numerics with 0
   │
   ▼
preprocessing.prepare_for_mongo()
   ├── Convert NaN → None
   └── Convert pd.Timestamp → Python datetime
   │
   ▼
validation.validate_batch()
   ├── Check required fields
   ├── Validate date range (2015–2030)
   ├── Check non-negative total_amount
   ├── Validate quantity > 0
   ├── Validate rating 0–5
   ├── Validate delivery_time 0–600
   └── Check order_status against known values
   │
   ├──▶ VALID records
   │         │
   │         ▼
   │    repositories.bulk_upsert_orders()
   │    (UpdateOne + upsert, ordered=False)
   │
   └──▶ REJECTED records → logged with reasons
   │
   ▼
repositories.log_import()
```

### Revenue Definition

**Realized Revenue** = SUM of `total_amount` WHERE `order_status` IN ("Completed", "Delivered")

Cancelled, Pending, and Processing orders are **excluded** from revenue calculations. This avoids inflating revenue with orders that were never fulfilled.

---

## 9. Key Aggregation Pipeline Examples

### Cancellation Rate
```python
pipeline = [
    {"$group": {
        "_id": None,
        "total": {"$sum": 1},
        "cancelled": {"$sum": {"$cond": [
            {"$in": ["$order_status", ["Cancelled", "Canceled"]]}, 1, 0
        ]}},
    }},
    {"$project": {
        "cancellation_rate": {"$multiply": [
            {"$divide": ["$cancelled", {"$max": ["$total", 1]}]}, 100
        ]}
    }}
]
```

### Delivery Time Buckets ($bucket)
```python
pipeline = [
    {"$match": {"delivery_time_minutes": {"$ne": None, "$gt": 0}}},
    {"$bucket": {
        "groupBy": "$delivery_time_minutes",
        "boundaries": [0, 15, 30, 45, 60, 90, 120, 180, 300],
        "default": "300+",
        "output": {"count": {"$sum": 1}}
    }}
]
```

### Order Activity Heatmap
```python
pipeline = [
    {"$group": {
        "_id": {
            "day": {"$dayOfWeek": "$order_date"},
            "hour": {"$hour": "$order_date"}
        },
        "orders": {"$sum": 1}
    }}
]
```

---

## 10. Implementation Details

### Deduplication Strategy
Orders are upserted using `UpdateOne({"order_id": id}, {"$setOnInsert": doc}, upsert=True)`. If a document with the same `order_id` already exists, it is neither overwritten nor duplicated — the `$setOnInsert` operator only executes on new documents.

### Caching
Streamlit's `@st.cache_data(ttl=120)` decorator caches aggregation results for 2 minutes. After a new import, caches are cleared with `st.cache_data.clear()`.

### Error Handling
- Database connection errors do not expose the connection URI in error messages.
- Import errors are collected per-record and surfaced in the import log and UI.
- Empty aggregation results return appropriate default values or empty-state charts.

---

## 11. Testing

### Test Coverage

| Test File | Tests | What Is Tested |
|-----------|-------|----------------|
| `test_validation.py` | 18 | Required fields, date validation, rating range, status values, batch processing |
| `test_metrics.py` | 7 | Revenue calculations, cancellation rate formula (mocked DB) |
| `test_aggregations.py` | 14 | Column normalisation, preprocessing, filter construction, CSV export |

### Running Tests
```powershell
pytest -q                          # All tests
pytest tests/test_validation.py -v # Verbose validation tests
```

Tests are designed to run **without** a live MongoDB connection. Database calls are mocked using `unittest.mock.patch`.

---

## 12. Performance Considerations

| Technique | Benefit |
|-----------|---------|
| Chunk-based import | Prevents memory exhaustion for large CSV files |
| `bulk_write` with `ordered=False` | Maximises write throughput; continues on individual errors |
| MongoDB aggregation pipelines | Computation at the database layer; minimal data transfer to Python |
| Compound indexes | Supports date+status filter combinations common in revenue queries |
| `$dateToString` in `$group` | Efficient date-based grouping without Python date parsing |
| Streamlit caching (TTL=120s) | Avoids re-querying unchanged data on every widget interaction |
| Pagination | Avoids loading all records into memory for the Data Explorer |

---

## 13. Advantages and Limitations

### Advantages
- Schema flexibility: new fields can be added to documents without altering a schema
- Aggregation framework is expressive and efficient for analytics workloads
- Streamlit enables rapid, interactive dashboard development
- Plotly provides publication-quality, interactive charts
- The modular architecture separates database, analytics, and UI concerns

### Limitations
- The sample dataset is synthetic; results are illustrative, not real business metrics
- MongoDB is not optimised for complex multi-collection JOIN operations
- Very complex statistical analysis (e.g., time-series forecasting) may require additional libraries
- Local deployment requires MongoDB to be installed and started separately

---

## 14. Future Enhancements

1. Real-time data ingestion via MongoDB Change Streams
2. Machine learning models for demand forecasting and delivery-time prediction
3. Authentication and role-based access (admin vs. viewer)
4. Automated report scheduling (PDF/email)
5. Multi-tenant support for different restaurant chains
6. Integration with a real food delivery platform API

---

## 15. Conclusion

This project successfully demonstrates a complete, end-to-end big data analytics pipeline for the online food delivery domain using MongoDB as the central data store. The system handles CSV ingestion with validation and deduplication, performs all analytical computations using MongoDB aggregation pipelines for scalability, and presents results through a professional interactive dashboard. The modular code architecture, comprehensive test suite, and thorough documentation make this project suitable for academic demonstration and as a foundation for further development.

---

## 16. References

1. MongoDB, Inc. (2024). *MongoDB Aggregation Pipeline*. https://www.mongodb.com/docs/manual/core/aggregation-pipeline/
2. Streamlit, Inc. (2024). *Streamlit Documentation*. https://docs.streamlit.io/
3. Plotly Technologies Inc. (2024). *Plotly Python Documentation*. https://plotly.com/python/
4. McKinney, W. (2022). *Python for Data Analysis*, 3rd Edition. O'Reilly Media.
5. Chodorow, K. (2013). *MongoDB: The Definitive Guide*. O'Reilly Media.
6. PyMongo Developers (2024). *PyMongo Documentation*. https://pymongo.readthedocs.io/

> **Note:** All performance figures and screenshots in this report should be updated with actual measurements from your deployed instance. The sample data is clearly marked as synthetic.

---

*Report prepared as part of the third-year B.E. Computer Science Engineering mini-project.*  
*Academic Year: 2024–2025*
