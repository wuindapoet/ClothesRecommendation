import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import json
import tensorflow as tf
import tensorflow_recommenders as tfrs
import numpy as np
import pandas as pd
from pathlib import Path

CLOTHING_TYPES = {
    "Shirts", "Tshirts", "Jeans", "Trousers", "Shorts",
    "Dresses", "Skirts", "Tops",
    "Kurtas", "Kurtis", "Tunics",
    "Sweaters", "Sweatshirts", "Jackets", "Rain Jacket",
    "Waistcoat", "Shrug",
    "Track Pants", "Tracksuits",
    "Night suits", "Nightdress",
    "Salwar", "Patiala", "Lehenga Choli", "Sarees",
    "Jeggings", "Leggings",
    "Rompers", "Swimwear",
    "Suits"
}

DATA_PATH = Path(__file__).parent / "styles.csv"
Columns = ['id', 'gender', 'articleType', 'season', 'usage']

df = pd.read_csv(DATA_PATH, usecols=Columns)
df = df.dropna()

df = df[df["articleType"].isin(CLOTHING_TYPES)]
df = df.reset_index(drop=True)

df['id'] = df['id'].astype(str)

data_dict = {
    "gender": df['gender'].values,
    "articleType": df['articleType'].values,
    "season": df['season'].values,
    "usage": df['usage'].values,
    "id": df['id'].values
}

dataset = tf.data.Dataset.from_tensor_slices(data_dict)

U_season = np.unique(data_dict['season'])
U_usage = np.unique(data_dict['usage'])
U_gender = np.unique(data_dict['gender'])
U_type = np.append(np.unique(data_dict['articleType']), "Unknown")
U_id = np.unique(data_dict['id'])

candidate_dataset = dataset.map(lambda x: {
    "id": x["id"],
    "gender": x["gender"],
    "articleType": x["articleType"],
    "season": x["season"],
    "usage": x["usage"],
})


Dimension = 32

class query(tf.keras.Model):
    def __init__(self):
        super().__init__()

        # DON'T name this one - it becomes "sequential" in the saved weights
        self.gender_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_gender, mask_token=None),
            tf.keras.layers.Embedding(len(U_gender) + 1, Dimension)
        ])

        # DON'T name this one - it becomes "sequential_1" in the saved weights
        self.deep_query = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32)
        ])

        # These MUST be created AFTER gender_embed and deep_query
        # They get their names from the attribute names
        self.usage_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_usage, mask_token=None),
            tf.keras.layers.Embedding(len(U_usage) + 1, Dimension)
        ])

        self.type_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_type, mask_token=None),
            tf.keras.layers.Embedding(len(U_type) + 1, Dimension)
        ])

        self.season_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_season, mask_token=None),
            tf.keras.layers.Embedding(len(U_season) + 1, Dimension)
        ])

    def call(self, inputs):
        x = tf.concat([
            self.gender_embed(inputs['gender']),
            self.usage_embed(inputs['usage']),
            self.type_embed(inputs['articleType']),
            self.season_embed(inputs['season'])
        ], axis=1)

        return tf.math.l2_normalize(self.deep_query(x), axis=1)

class candidate(tf.keras.Model):
    def __init__(self):
        super().__init__()

        self.id_proj = tf.keras.layers.Dense(32)
        
        # DON'T name this - becomes "sequential"
        self.id_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_id, mask_token=None),
            tf.keras.layers.Embedding(len(U_id) + 1, Dimension * 4)
        ])

        # DON'T name this - becomes "sequential_1"
        self.gender_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_gender, mask_token=None),
            tf.keras.layers.Embedding(len(U_gender) + 1, Dimension)
        ])

        # DON'T name this - becomes "sequential_2"
        self.deep_cand = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32)
        ])

        # These get named from attributes
        self.usage_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_usage, mask_token=None),
            tf.keras.layers.Embedding(len(U_usage) + 1, Dimension)
        ])

        self.type_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_type, mask_token=None),
            tf.keras.layers.Embedding(len(U_type) + 1, Dimension)
        ])

        self.season_embed = tf.keras.Sequential([
            tf.keras.layers.StringLookup(vocabulary=U_season, mask_token=None),
            tf.keras.layers.Embedding(len(U_season) + 1, Dimension)
        ])

    def call(self, inputs):
        content = tf.concat([
            self.gender_embed(inputs['gender']),
            self.usage_embed(inputs['usage']),
            self.type_embed(inputs['articleType']),
            self.season_embed(inputs['season']),
        ], axis=1)

        content_vec = self.deep_cand(content)      # (B, 32)
        id_vec = self.id_embed(inputs["id"])        # (B, 128)
        id_vec = self.id_proj(id_vec)               # (B, 32)

        return tf.math.l2_normalize(content_vec + id_vec, axis=1)
    
class main_model(tfrs.Model):
    def __init__(self, with_metrics=False):
        super().__init__()
        self.query_model = query()
        self.candidate_model = candidate()

        if with_metrics:
            self.task = tfrs.tasks.Retrieval(
                metrics=tfrs.metrics.FactorizedTopK(
                    candidates=candidate_dataset
                        .batch(128)
                        .map(self.candidate_model)
                        .cache()
                )
            )
        else:
            self.task = tfrs.tasks.Retrieval()

    def compute_query_embeddings(self, features):
        return self.query_model(features)

    def compute_candidate_embeddings(self, features):
        return self.candidate_model(features)

    def call(self, features):
        query_embed = self.compute_query_embeddings(features)
        candidate_embed = self.compute_candidate_embeddings(features)
        return query_embed, candidate_embed

    def compute_loss(self, features, training=False):
        query_embed, candidate_embed = self(features)
        return self.task(query_embed, candidate_embed)


class RecommendationEngine:
    def __init__(self):
        self.model = None
        self.index = None
        self.all_identifiers = None
        self.df = None

    def load_model_and_index(self):
        """Load model and build index once at startup"""
        print("Loading model...")
        self.model = main_model(with_metrics=False)

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam()
        )

        WEIGHT_PATH = Path(__file__).parent / "model.weights.h5"
        self.model.load_weights(WEIGHT_PATH)

        print("Model loaded successfully!")

        self.df = df.set_index("id")

        # safety filter (should be redundant but keeps system robust)
        self.df = self.df[self.df["articleType"].isin(CLOTHING_TYPES)]

        print(f"Metadata loaded: {len(self.df)} items")

        # Build the index once
        print("Building recommendation index...")
        self.index = tfrs.layers.factorized_top_k.BruteForce(
            self.model.compute_query_embeddings
        )

        # Get candidate dataset
        candidate_dataset = tf.data.Dataset.from_tensor_slices(data_dict)

        # Pre-calculate all embeddings
        print("Calculating candidate embeddings...")
        self.index = tfrs.layers.factorized_top_k.BruteForce(
            self.model.compute_query_embeddings
        )

        self.index.index_from_dataset(
            candidate_dataset.batch(128).map(
                lambda x: (
                    x["id"],
                    self.model.compute_candidate_embeddings(x)
                )
            )
        )

        print("Index built successfully!")

    def predict(self, user_inputs, k=5):
        """
        Return full recommendation info
        """
        if self.model is None or self.index is None:
            raise RuntimeError("Model not loaded. Call load_model_and_index() first.")
        
        preferred_type = "Shirts" if user_inputs["usage"] == "Formal" else "Tshirts"
        # Build query
        user_query = {
            "gender": tf.constant([user_inputs['gender']]),
            "articleType": tf.constant([preferred_type]),
            "season": tf.constant([user_inputs['season']]),
            "usage": tf.constant([user_inputs['usage']])
        }

        # Retrieve top-K
        RETRIEVE_K = max(k * 10, 50)
        scores, top_ids = self.index(user_query, k=RETRIEVE_K)

        # Build response with metadata
        results = []

        expected_usage = user_inputs["usage"]
        expected_season = user_inputs["season"]

        primary = []
        secondary = []
        fallback = []

        score_min = float(tf.reduce_min(scores))
        score_max = float(tf.reduce_max(scores))

        for rank, raw_id in enumerate(top_ids[0].numpy()):
            item_id = raw_id.decode("utf-8")
            meta = self.df.loc[item_id]

            if expected_usage == "Formal":
                if meta["articleType"] in [
                    "Bra", "Briefs", "Innerwear", "Lingerie",
                    "Socks", "Caps", "Flip Flops"
                ]:
                    continue

            if expected_usage == "Casual":
                if meta["articleType"] in [
                    "Bra", "Briefs", "Innerwear"
                ]:
                    continue

            raw_score = float(scores[0][rank].numpy())
            embedding_score = (raw_score - score_min) / (score_max - score_min + 1e-8)

            usage_match = 1 if meta["usage"] == expected_usage else 0
            season_match = 1 if meta["season"] == expected_season else 0

            final_score = (
                0.20 * embedding_score +
                0.50 * usage_match +
                0.20 * season_match
            )

            item = {
                "id": item_id,
                "type": meta["articleType"],
                "gender": meta["gender"],
                "season": meta["season"],
                "usage": meta["usage"],
                "image": f"/static/images/{item_id}.jpg",
                "score": round(final_score, 4),
                "debug": {
                    "embedding": round(embedding_score, 4),
                    "usage_match": usage_match,
                    "season_match": season_match,
                }
            }

            # TIER 1: usage + season
            season_ok = meta["season"] in [expected_season, "All"]
            if (meta["usage"] == expected_usage and season_ok):
                primary.append(item)

            # TIER 2: match usage
            elif meta["usage"] == expected_usage:
                secondary.append(item)

            # TIER 3: fallback (similarity only)
            else:
                fallback.append(item)

        results = primary + secondary
        if len(results) < k:
            results += fallback

        results = sorted(results, key=lambda x: x["score"], reverse=True)

        return results[:k]