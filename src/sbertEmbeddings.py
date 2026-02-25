from sentence_transformers import SentenceTransformer, util
import json

# Global variable to store the model instance
model = None

def get_sbert_model():
    """
    Lazily load and return the SBERT model.
    """
    global model
    if model is None:
        print("Loading SBERT model...")
        model = SentenceTransformer('msmarco-distilbert-cos-v5')
        print("SBERT model loaded successfully!")
    return model

def calculate_similarity_and_rank(json_data):
    """
    Calculate cosine similarity between the README and tokenized class names,
    and rank the classes by similarity score.
    """

    print(json.dumps(json_data, indent=4))

    # Step 1: Load the SBERT model
    sbert_model = get_sbert_model()

    # Step 2: Embed the README
    readme = json_data["readme"]

    print("Embedding the readme")
    readme_embedding = sbert_model.encode(readme)
    print("ok!\n")

    
    # Step 3: Embed the tokenized class names
    tokenized_classes = json_data["tokenized_class_names"]
    tokenized_class_names = list(tokenized_classes.values())
    original_class_names = list(tokenized_classes.keys())

    # Batch embed the tokenized class names
    class_embeddings = sbert_model.encode(tokenized_class_names)

    # Step 4: Calculate cosine similarity
    similarity_scores = util.cos_sim(readme_embedding, class_embeddings)[0]

    # Step 5: Rank the classes by similarity score
    ranked_classes = [
        (original_class_names[i], tokenized_class_names[i], similarity_scores[i].item())
        for i in range(len(original_class_names))
    ]
    ranked_classes.sort(key=lambda x: x[2], reverse=True)

    # Step 6: Update JSON structure
    json_data["ranked_classes"] = [name for _, name, _ in ranked_classes]

    return json_data


# test the file locally using main and example in JSON format
if __name__ == "__main__":
    # Usage example
    json_data = {
        "readme": "a fleet management system that handles car services and rentals",
        "tokenized_class_names": {"fleetManagement": "fleet management", "carWash": "car wash"}
    }

    # Calculate similarity and rank classes
    json_data = calculate_similarity_and_rank(json_data)

    # Output the updated json_data
    print(json_data)
