import math
from typing import Dict, List, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text


def _wkt_point(lon: float, lat: float) -> str:
    return f"SRID=4326;POINT({lon} {lat})"


def get_nearby_shops(db: Session, lat: float, lon: float, radius_km: float) -> List[Tuple[dict, float, float, float]]:
    radius_m = float(radius_km) * 1000.0
    q = text(
        """
        SELECT s.id, s.name, s.address,
               ST_Distance(s.location, ST_GeogFromText(:wkt)) AS distance_m,
               ST_Y(ST_Transform(s.location::geometry, 4326)) AS lat,
               ST_X(ST_Transform(s.location::geometry, 4326)) AS lon
        FROM shops s
        WHERE ST_DWithin(s.location, ST_GeogFromText(:wkt), :radius)
        ORDER BY distance_m
        LIMIT 200
        """
    )
    rows = db.execute(q, {"wkt": _wkt_point(lon, lat), "radius": radius_m}).mappings().all()
    result: List[Tuple[dict, float, float, float]] = []
    for r in rows:
        shop = {"id": r["id"], "name": r["name"], "address": r["address"]}
        d_km = float(r["distance_m"]) / 1000.0 if r["distance_m"] is not None else None
        result.append((shop, d_km or 0.0, float(r["lat"]) if r["lat"] is not None else None, float(r["lon"]) if r["lon"] is not None else None))
    return result


def get_user_top_categories(db: Session, user_id: int) -> Dict[int, float]:
    q = text(
        """
        WITH views AS (
            SELECT p.category_id, COUNT(*)::float AS score
            FROM product_view_events e
            JOIN products p ON p.id = e.product_id
            WHERE e.user_id = :uid AND p.category_id IS NOT NULL
            GROUP BY p.category_id
        ),
        purchases AS (
            SELECT p.category_id, COALESCE(SUM(GREATEST(pe.quantity,1)) * 2.0, 0)::float AS score
            FROM purchase_events pe
            JOIN products p ON p.id = pe.product_id
            WHERE pe.user_id = :uid AND p.category_id IS NOT NULL
            GROUP BY p.category_id
        ),
        merged AS (
            SELECT category_id, SUM(score) AS score
            FROM (
                SELECT * FROM views
                UNION ALL
                SELECT * FROM purchases
            ) u
            GROUP BY category_id
        )
        SELECT category_id, score
        FROM merged
        ORDER BY score DESC
        """
    )
    rows = db.execute(q, {"uid": user_id}).all()
    if not rows:
        return {}
    max_score = max(r[1] for r in rows) or 1.0
    return {int(r[0]): float(r[1]) / max_score for r in rows}


def _trending_score(daily_views: int, weekly_sales: int) -> float:
    a, b = 0.6, 0.8
    dv = max(0, daily_views or 0)
    ws = max(0, weekly_sales or 0)
    return a * math.log1p(dv) + b * math.log1p(ws)


def _proximity_factor(distance_m: float) -> float:
    # Closer shops receive higher multiplicative factor; ~500m scale
    return 1.0 / (1.0 + (float(distance_m) / 500.0))


def recommend_products(
    db: Session,
    user_id: int,
    lat: float,
    lon: float,
    radius_km: float = 5.0,
    limit: int = 20,
):
    nearby = get_nearby_shops(db, lat, lon, radius_km)
    if not nearby:
        return [], []

    shop_ids = [s[0]["id"] for s in nearby]
    distance_by_shop_km = {s[0]["id"]: s[1] for s in nearby}

    user_cat_weights = get_user_top_categories(db, user_id)

    # Fetch candidate products from nearby shops
    q = text(
        """
        SELECT p.id, p.name, p.category_id, p.shop_id,
               COALESCE(p.daily_views, 0) AS daily_views,
               COALESCE(p.weekly_sales, 0) AS weekly_sales
        FROM products p
        WHERE p.shop_id = ANY(:shop_ids)
        """
    )
    rows = db.execute(q, {"shop_ids": shop_ids}).mappings().all()

    recs: List[dict] = []
    for r in rows:
        cat_score = user_cat_weights.get(r["category_id"], 0.0)
        trending = _trending_score(int(r["daily_views"]), int(r["weekly_sales"]))
        dist_km = float(distance_by_shop_km.get(r["shop_id"], 10.0))
        prox = _proximity_factor(dist_km * 1000.0)
        score = 0.6 * cat_score + 0.3 * trending + 0.1 * prox

        recs.append({
            "product_id": int(r["id"]),
            "product_name": r["name"],
            "shop_id": int(r["shop_id"]),
            "category_id": int(r["category_id"]) if r["category_id"] is not None else None,
            "score": float(score),
            "reasons": ["matches_recent_preferences"] if cat_score > 0 else None,
        })

    recs.sort(key=lambda x: x["score"], reverse=True)

    shops_out = []
    for shop, d_km, lat_val, lon_val in nearby:
        shops_out.append({
            "id": shop["id"],
            "name": shop["name"],
            "address": shop["address"],
            "distance_km": round(d_km, 3),
            "latitude": lat_val,
            "longitude": lon_val,
        })

    return shops_out, recs[:limit]
