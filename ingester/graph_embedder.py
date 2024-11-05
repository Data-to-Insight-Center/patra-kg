import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

def open_ai_embedding(model_card, fields=None):
    if fields is None:
        fields = ['author', 'short_description', 'full_description', 'version', "input_type", "keywords", "category",
                  "input_data"]
    tokenized_text = " ".join(str(model_card[field]) for field in fields if field in model_card)

    response = client.embeddings.create(
        input=tokenized_text,
        model="text-embedding-3-small",
        encoding_format="float",
        dimensions=300
    )

    return response.data[0].embedding


def embed_query(query):
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small",
        encoding_format="float",
        dimensions=300
    )
    return response.data[0].embedding


def embed_model_versioning(model_card, fields=None):
    if fields is None:
        fields = ['author', 'short_description', 'full_description', 'version', "input_type", "keywords", "category",
                  "input_data"]
    return open_ai_embedding(model_card, fields)
