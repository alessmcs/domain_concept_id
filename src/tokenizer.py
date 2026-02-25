import re
import nltk
from nltk.corpus import stopwords

# Ensure the stopwords are downloaded (run only if not downloaded already)
try:
    # Try to find the 'stopwords' corpus
    nltk.data.find('corpora/stopwords')
except LookupError:
    # If not found, download the stopwords corpus
    nltk.download('stopwords')

nltk_stop_words = set(stopwords.words("english"))

def tokenize_class_name(class_name):
    """
    Tokenize a single class name by splitting camelCase, PascalCase, or snake_case
    into lowercase tokens and removing stop words.

    Args:
        class_name (str): The class name to tokenize.

    Returns:
        str: The tokenized class name as a string.
    """
    # Split class name based on uppercase letters or underscores
    tokens = re.findall(r'[A-Z][a-z]*|[a-z]+|\d+|[A-Z]+', class_name)
    # Convert to lowercase and remove stop words
    tokens = [token.lower() for token in tokens if token.lower() not in nltk_stop_words]
    # Join tokens with a space
    return " ".join(tokens)

def tokenize_class_names(class_names):
    """
    Tokenize a list of class names.

    Args:
        class_names (list): A list of class names.

    Returns:
        dict: A dictionary mapping original class names to tokenized versions.
    """
    return {name: tokenize_class_name(name) for name in class_names}

if __name__ == "__main__":
    # Example usage for testing
    class_names = ["Fleet_Service_Type", "test_RentType", "VehicleDamage_Type"]
    tokenized = tokenize_class_names(class_names)
    print(tokenized)

