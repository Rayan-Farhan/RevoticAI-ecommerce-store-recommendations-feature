"""
Functionality of this script:
Train item-based KNN using sklearn on a sparse user-item matrix and store top-K neighbors
in item_similarity table.
"""

import math
from collections import defaultdict
from sqlalchemy import text
from app.db import SessionLocal
from app.models.recommendation import ItemSimilarity
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, csr_matrix
from sklearn.neighbors import NearestNeighbors
import os

TOP_K = 10       # how many neighbors per item
KNN_K = TOP_K + 1  # NearestNeighbors returns self as neighbor; request one extra

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

def build_sparse_matrix(df):
    # Map user_id and product_id to indices
    user_ids = df["user_id"].unique().tolist()
    item_ids = df["product_id"].unique().tolist()
    user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
    item_to_idx = {pid: j for j, pid in enumerate(item_ids)}

    row = df["user_id"].map(user_to_idx).to_numpy()
    col = df["product_id"].map(item_to_idx).to_numpy()
    data = df["weight"].to_numpy(dtype=float)

    # build user-item matrix
    mat = coo_matrix((data, (row, col)), shape=(len(user_ids), len(item_ids))).tocsr()
    return mat, user_ids, item_ids, user_to_idx, item_to_idx

def train_and_store(k_neighbors=TOP_K):
    db = SessionLocal()
    print("Loading interactions from DB...")
    df = load_interactions(db)
    if df.empty:
        print("No interaction data found. Nothing to train.")
        db.close()
        return

    print(f"Interactions rows: {len(df)}")
    M, user_ids, item_ids, user_to_idx, item_to_idx = build_sparse_matrix(df)
    print(f"user_count={len(user_ids)}, item_count={len(item_ids)}")
    # items as samples: transpose -> shape (n_items, n_users)
    item_matrix = M.T.tocsr()

    # NearestNeighbors with cosine metric returns distances in [0, 2] for sparse
    print("Fitting NearestNeighbors on item vectors (cosine) ...")
    nn = NearestNeighbors(n_neighbors=min(KNN_K, item_matrix.shape[0]), metric="cosine", algorithm="brute", n_jobs=-1)
    nn.fit(item_matrix)

    print("Computing neighbors (in batches)...")
    # Query all neighbors (returns distances)
    distances, indices = nn.kneighbors(item_matrix, return_distance=True)

    # Prepare bulk insert objects
    bulk_objs = []
    total_items = item_matrix.shape[0]
    for i in range(total_items):
        raw_item_id = item_ids[i]
        neigh_idxs = indices[i]
        neigh_dists = distances[i]
        for idx_j, dist in zip(neigh_idxs, neigh_dists):
            # skip self
            if idx_j == i:
                continue
            sim_score = 1.0 - float(dist)  # cosine similarity = 1 - cosine_distance
            neighbor_item_id = item_ids[idx_j]
            bulk_objs.append(ItemSimilarity(item_id=int(raw_item_id),
                                            similar_item_id=int(neighbor_item_id),
                                            score=float(sim_score)))
        # commit in batches to avoid super large transactions
        if (i + 1) % 500 == 0 and bulk_objs:
            # truncate before first bulk insert (only once)
            if i < 500:
                db.execute(text("TRUNCATE TABLE item_similarity RESTART IDENTITY;"))
                db.commit()
            db.bulk_save_objects(bulk_objs)
            db.commit()
            bulk_objs = []
            print(f"Stored neighbors for {i+1}/{total_items} items...")

    # final commit
    if bulk_objs:
        # ensure truncation if matrix smaller than batch threshold
        if total_items < 500:
            db.execute(text("TRUNCATE TABLE item_similarity RESTART IDENTITY;"))
            db.commit()
        db.bulk_save_objects(bulk_objs)
        db.commit()

    print("Item similarity training complete and stored to DB.")
    db.close()

if __name__ == "__main__":
    train_and_store()