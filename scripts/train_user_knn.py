"""
Functionality of this script:
Train user-based KNN using sklearn on a sparse user-item matrix and store top-K neighbors
in user_similarity table.
"""

from sqlalchemy import text
from app.db import SessionLocal
from app.models.recommendation import UserSimilarity
import pandas as pd
from scipy.sparse import coo_matrix
from sklearn.neighbors import NearestNeighbors

TOP_K = 10
KNN_K = TOP_K + 1

def load_interactions(db):
    q = text("""
        SELECT user_id, product_id, 1.0 AS weight
        FROM product_view_events
        UNION ALL
        SELECT user_id, product_id, (quantity * 3.0) AS weight
        FROM purchase_events
    """)
    rows = db.execute(q).fetchall()
    if not rows:
        return pd.DataFrame(columns=["user_id", "product_id", "weight"])
    return pd.DataFrame(rows, columns=["user_id", "product_id", "weight"])

def build_user_item(df):
    user_ids = df["user_id"].unique().tolist()
    item_ids = df["product_id"].unique().tolist()
    user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
    item_to_idx = {pid: j for j, pid in enumerate(item_ids)}

    row = df["user_id"].map(user_to_idx).to_numpy()
    col = df["product_id"].map(item_to_idx).to_numpy()
    data = df["weight"].to_numpy(dtype=float)

    mat = coo_matrix((data, (row, col)), shape=(len(user_ids), len(item_ids))).tocsr()
    return mat, user_ids, item_ids

def train_and_store(k_neighbors=TOP_K):
    db = SessionLocal()
    df = load_interactions(db)
    if df.empty:
        print("No interaction data. Exiting.")
        db.close()
        return

    M, user_ids, item_ids = build_user_item(df)
    print(f"user_count={len(user_ids)}, item_count={len(item_ids)}")

    # users as samples: M (n_users x n_items)
    user_matrix = M

    print("Fitting NearestNeighbors on user vectors (cosine)...")
    nn = NearestNeighbors(n_neighbors=min(KNN_K, user_matrix.shape[0]), metric="cosine", algorithm="brute", n_jobs=-1)
    nn.fit(user_matrix)

    distances, indices = nn.kneighbors(user_matrix, return_distance=True)

    # bulk store
    bulk_objs = []
    total_users = user_matrix.shape[0]
    for i in range(total_users):
        raw_user_id = user_ids[i]
        neigh_idxs = indices[i]
        neigh_dists = distances[i]
        for idx_j, dist in zip(neigh_idxs, neigh_dists):
            if idx_j == i:
                continue
            sim_score = 1.0 - float(dist)
            neighbor_user_id = user_ids[idx_j]
            bulk_objs.append(UserSimilarity(user_id=int(raw_user_id),
                                            similar_user_id=int(neighbor_user_id),
                                            score=float(sim_score)))
        if (i + 1) % 500 == 0 and bulk_objs:
            if i < 500:
                db.execute(text("TRUNCATE TABLE user_similarity RESTART IDENTITY;"))
                db.commit()
            db.bulk_save_objects(bulk_objs)
            db.commit()
            bulk_objs = []
            print(f"Stored neighbors for {i+1}/{total_users} users...")

    if bulk_objs:
        if total_users < 500:
            db.execute(text("TRUNCATE TABLE user_similarity RESTART IDENTITY;"))
            db.commit()
        db.bulk_save_objects(bulk_objs)
        db.commit()

    print("User similarity training complete and stored to DB.")
    db.close()

if __name__ == "__main__":
    train_and_store()