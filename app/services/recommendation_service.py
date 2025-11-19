# app/services/recommendation_service.py
import math
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from collections import defaultdict


# ------------------------------
# Utility functions
# ------------------------------
def _wkt_point(lon: float, lat: float) -> str:
    return f"SRID=4326;POINT({lon} {lat})"

def _trending_score(daily_views, weekly_sales):
    return math.log1p(daily_views or 0) + math.log1p(weekly_sales or 0)

def _proximity_factor(distance_km: float) -> float:
    return 1.0 / (1.0 + (distance_km / 0.5))


# ------------------------------
# Nearby shops (PostGIS)
# ------------------------------
def get_nearby_shops_service(db: Session, lat: float, lon: float, radius_km: float = 5.0):
    q = text("""
        SELECT s.id, s.name, s.address,
               ST_Distance(s.location, ST_GeogFromText(:wkt)) AS distance_m,
               ST_Y(ST_Transform(s.location::geometry, 4326)) AS lat,
               ST_X(ST_Transform(s.location::geometry, 4326)) AS lon
        FROM shops s
        WHERE ST_DWithin(s.location, ST_GeogFromText(:wkt), :radius)
        ORDER BY distance_m
        LIMIT 200;
    """)

    rows = db.execute(q, {
        "wkt": _wkt_point(lon, lat),
        "radius": float(radius_km) * 1000
    }).mappings().all()

    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "name": r["name"],
            "address": r["address"],
            "distance_km": round(float(r["distance_m"]) / 1000, 3),
            "latitude": float(r["lat"]),
            "longitude": float(r["lon"])
        })
    return out


# ------------------------------
# User category preferences
# ------------------------------
def get_user_top_categories(db: Session, user_id: int):
    q = text("""
        WITH views AS (
            SELECT p.category_id, COUNT(*)::float AS score
            FROM product_view_events e
            JOIN products p ON p.id = e.product_id
            WHERE e.user_id = :u AND p.category_id IS NOT NULL
            GROUP BY p.category_id
        ),
        purchases AS (
            SELECT p.category_id, SUM(GREATEST(pe.quantity, 1)) * 2.0 AS score
            FROM purchase_events pe
            JOIN products p ON p.id = pe.product_id
            WHERE pe.user_id = :u AND p.category_id IS NOT NULL
            GROUP BY p.category_id
        ),
        merged AS (
            SELECT category_id, SUM(score) AS score
            FROM (
                SELECT * FROM views
                UNION ALL
                SELECT * FROM purchases
            ) x
            GROUP BY category_id
        )
        SELECT category_id, score
        FROM merged
        ORDER BY score DESC;
    """)

    rows = db.execute(q, {"u": user_id}).fetchall()
    if not rows:
        return {}

    max_score = max(r[1] for r in rows)
    return {r[0]: float(r[1]) / max_score for r in rows}


# ------------------------------
# Hybrid product recommender
# ------------------------------
def recommend_products_hybrid(db: Session, user_id: int, lat: float, lon: float, radius_km: float = 5.0, limit=20):
    # 1) Nearby shops
    shops = get_nearby_shops_service(db, lat, lon, radius_km)
    if not shops:
        return [], []

    shop_ids = [s["id"] for s in shops]
    dist_by_shop = {s["id"]: s["distance_km"] for s in shops}

    # 2) User category preference
    user_cat_weights = get_user_top_categories(db, user_id)

    # 3) Candidate products (in nearby shops)
    q = text("""
        SELECT p.id,
               p.name,
               p.category_id,
               p.shop_id,
               COALESCE(p.daily_views,0)  AS daily_views,
               COALESCE(p.weekly_sales,0) AS weekly_sales
        FROM products p
        WHERE p.shop_id = ANY(:shops);
    """)

    rows = db.execute(q, {"shops": shop_ids}).mappings().all()
    candidate_ids = [r["id"] for r in rows]

    # 4) CF score via stored KNN similarities
    cf_scores = {}
    if candidate_ids:
        sim_q = text("""
            SELECT similar_item_id AS cid, MAX(score) AS sc
            FROM item_similarity
            WHERE similar_item_id = ANY(:cands)
            AND item_id IN (
                SELECT product_id FROM product_view_events WHERE user_id = :u
                UNION
                SELECT product_id FROM purchase_events WHERE user_id = :u
            )
            GROUP BY similar_item_id;
        """)
        sim_rows = db.execute(sim_q, {"cands": candidate_ids, "u": user_id}).fetchall()
        cf_scores = {r[0]: float(r[1]) for r in sim_rows}

    # 5) Final scoring
    recs = []
    for r in rows:
        pid = r["id"]
        cat = r["category_id"]
        shop = r["shop_id"]

        cat_score = user_cat_weights.get(cat, 0.0)
        trending = _trending_score(r["daily_views"], r["weekly_sales"])
        prox = _proximity_factor(dist_by_shop.get(shop, radius_km))
        cf = cf_scores.get(pid, 0.0)

        final_score = (
            0.35 * cat_score +
            0.25 * (trending / (1 + trending)) +
            0.10 * prox +
            0.30 * cf
        )

        recs.append({
            "product_id": pid,
            "product_name": r["name"],
            "shop_id": shop,
            "category_id": cat,
            "score": final_score,
            "cf_score": cf
        })

    recs.sort(key=lambda x: x["score"], reverse=True)

    return shops, recs[:limit]