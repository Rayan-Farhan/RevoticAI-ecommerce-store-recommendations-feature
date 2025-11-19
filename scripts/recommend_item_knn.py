"""
Functionality of this script:
Produce top-N item recommendations for a specific user_id using item_similarity table.
Usage:
    python scripts/recommend_item_knn.py <user_id> [--limit 5]
"""

import argparse
from collections import defaultdict
from sqlalchemy import text
from app.db import SessionLocal

def get_user_seen_items(db, user_id):
    q = text("""
        SELECT DISTINCT product_id
        FROM (
            SELECT product_id FROM product_view_events WHERE user_id = :u
            UNION
            SELECT product_id FROM purchase_events WHERE user_id = :u
        ) x
    """)
    rows = db.execute(q, {"u": user_id}).fetchall()
    return set(r[0] for r in rows)

def get_similar_items_for_items(db, item_ids):
    if not item_ids:
        return {}
    q = text("""
        SELECT item_id, similar_item_id, score
        FROM item_similarity
        WHERE item_id = ANY(:ids)
    """)
    rows = db.execute(q, {"ids": list(item_ids)}).fetchall()
    d = defaultdict(list)
    for item_id, sim_id, score in rows:
        d[item_id].append((sim_id, float(score)))
    return d

def get_product_details(db, pids):
    if not pids:
        return {}
    q = text("""
        SELECT id, name, shop_id, category_id
        FROM products
        WHERE id = ANY(:ids)
    """)
    rows = db.execute(q, {"ids": list(pids)}).fetchall()
    return {r[0]: {"name": r[1], "shop_id": r[2], "category_id": r[3]} for r in rows}

def recommend_top_k(db, user_id, limit=5):
    seen = get_user_seen_items(db, user_id)
    if not seen:
        # fallback to top trending products
        q = text("SELECT id, name FROM products ORDER BY weekly_sales DESC, daily_views DESC LIMIT :l")
        rows = db.execute(q, {"l": limit}).fetchall()
        return [{"product_id": r[0], "product_name": r[1], "score": None} for r in rows]

    similar = get_similar_items_for_items(db, list(seen))
    score_agg = defaultdict(float)
    # aggregate neighbor scores
    for base_item, neighbors in similar.items():
        for sim_id, score in neighbors:
            if sim_id in seen:
                continue
            score_agg[sim_id] += score

    if not score_agg:
        q = text("SELECT id, name FROM products ORDER BY weekly_sales DESC, daily_views DESC LIMIT :l")
        rows = db.execute(q, {"l": limit}).fetchall()
        return [{"product_id": r[0], "product_name": r[1], "score": None} for r in rows]

    ranked = sorted(score_agg.items(), key=lambda x: x[1], reverse=True)[:limit]
    pids = [pid for pid, _ in ranked]
    details = get_product_details(db, pids)

    results = []
    for pid, sc in ranked:
        det = details.get(pid, {})
        results.append({
            "product_id": pid,
            "product_name": det.get("name"),
            "shop_id": det.get("shop_id"),
            "category_id": det.get("category_id"),
            "score": round(sc, 6)
        })
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id", type=int)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    db = SessionLocal()
    recs = recommend_top_k(db, args.user_id, args.limit)
    print(f"Top {args.limit} recommendations for user {args.user_id}:")
    for i, r in enumerate(recs, 1):
        print(f"{i}. {r['product_name']} (id={r['product_id']}) score={r['score']}")
    db.close()