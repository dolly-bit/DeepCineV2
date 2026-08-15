import faiss
import numpy as np

# Load embeddings
embeddings = np.load("movie_embeddings.npy").astype("float32")

# Create FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])

# Add embeddings
index.add(embeddings)

# Save index
faiss.write_index(index, "movie_index.faiss")

print(f"FAISS index created with {index.ntotal} movies.")