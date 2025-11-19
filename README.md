Grocery Platform — Recommendations Feature (FastAPI)
===================================================

This module provides location-aware shop recommendations and hybrid product recommendations
for a grocery e-commerce store, using PostgreSQL + PostGIS and collaborative filtering.

Directory structure
-------------------

```
app/
	__init__.py
	db.py              # SQLAlchemy engine and SessionLocal
	main.py            # FastAPI app entrypoint
	models/
		__init__.py
		recommendation.py  # ORM models for item/user similarity tables
	routers/
		__init__.py
		recommendations.py # /recommend/shops and /recommend/products endpoints
	schemas/
		__init__.py
		product.py        # Product response schemas (if needed elsewhere)
		recommendation.py # ShopOut, ProductOut, ProductRecommendationsResponse
		shop.py           # Basic ShopBase schema
	services/
		__init__.py
		recommendation_service.py # Geo + hybrid recommendation logic

scripts/
	__init__.py
	schema.sql          # DDL for users, shops, products, events, similarity tables
	seed.sql            # Demo users, shops, products, interaction events
	init_db.py          # Helper to apply schema.sql and seed.sql via psql
	train_item_knn.py   # Offline item-based KNN training -> item_similarity
	train_user_knn.py   # Offline user-based KNN training -> user_similarity
	recommend_item_knn.py # CLI to inspect item-based recommendations

requirements.txt
.env
```

How it works
------------

- Shops are stored with PostGIS geography points (`shops.location`).
- `/recommend/shops` returns nearby shops ordered by distance from the given
	latitude/longitude using `ST_DWithin` and `ST_Distance`.
- Product recommendations combine:
	- Trending score from `products.daily_views` and `products.weekly_sales`.
	- User category preferences derived from `product_view_events` and
		`purchase_events`.
	- Proximity to the user’s nearby shops.
	- Item-based collaborative filtering scores from the `item_similarity` table,
		trained offline with KNN over a user–item interaction matrix.

Run instructions (Windows PowerShell)
-------------------------------------

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Ensure PostgreSQL with PostGIS is available, and configure `.env` or
	 environment with `DATABASE_URL` pointing to your database.

3. Initialize schema and seed demo data:

```powershell
python scripts\init_db.py
```

4. Train collaborative filtering models:

```powershell
python -m scripts.train_item_knn
python -m scripts.train_user_knn
```

5. Run the API server:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Example requests:

- Nearby shops:

	`GET /recommend/shops?lat=24.8607&lon=67.0011&radius_km=5`

- Hybrid product recommendations:

	`GET /recommend/products?user_id=1&lat=24.8607&lon=67.0011&radius_km=5&limit=20`