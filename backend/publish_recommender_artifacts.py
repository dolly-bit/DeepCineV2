"""Publish the locally built content-recommender index to private GCS.

Run from the backend directory after building and validating the index:
    python publish_recommender_artifacts.py
"""
import logging

from ai.artifact_storage import publish_artifacts_to_gcs

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

if __name__ == "__main__":
    publish_artifacts_to_gcs()
    print("Recommender artifacts published successfully.")
