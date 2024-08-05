import numpy as np
import time
from openai import OpenAI
import os
from dotenv import load_dotenv

# load_dotenv()

# glove2word2vec(glove_input_file="../ingester/glove.6B.200d.txt", word2vec_output_file="gensim_glove_vectors.txt")
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# llama 3 through Ollama


# Load pre-trained BERT model and tokenizer
# bert_model_name = 'bert-base-uncased'
# bert_model = BertModel.from_pretrained(bert_model_name)
# bert_tokenizer = BertTokenizer.from_pretrained(bert_model_name)

# def get_bert_embeddings(fields, model_card, model, tokenizer):
#     text = " ".join(str(model_card[field]) for field in fields if field in model_card)
#     tokens = tokenizer.tokenize(text)
#     tokens = ['[CLS]'] + tokens + ['[SEP]']
#     token_ids = tokenizer.convert_tokens_to_ids(tokens)
#     token_ids_tensor = torch.tensor([token_ids])
#
#     attention_mask = torch.tensor([[1]*len(token_ids)])
#
#     with torch.no_grad():
#         outputs = model(token_ids_tensor, attention_mask=attention_mask)
#         embeddings = outputs.last_hidden_state[0]
#
#     sentence_embedding = torch.mean(embeddings, dim=0)
#     return sentence_embedding


# def embed_glove_versioning(model_card, fields=None):
#     # Load the GloVe model
#     glove_model = KeyedVectors.load_word2vec_format(
#         datapath('/Users/swithana/git/ai-model-cards/workload_generator/gensim_glove_vectors.txt'), binary=False)
#
#     # Select textual fields for comparison
#     if fields is None:
#         fields = ['author', 'short_description', 'full_description', 'version', "input_type", "keywords", "category",
#                   "input_data"]
#
#     embeddings = []
#     for field in fields:
#         text = model_card.get(field, "")
#         tokens = text.lower().split()
#         word_embeddings = [glove_model.get_vector(token) for token in tokens if token in glove_model.key_to_index]
#         if word_embeddings:
#             embeddings.append(np.mean(word_embeddings, axis=0))
#
#     if embeddings:
#         combined_embedding = np.mean(embeddings, axis=0)
#     else:
#         combined_embedding = np.zeros(glove_model.vector_size)
#
#     return combined_embedding


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


# def llama3_embedding(model_card, fields, llm='llama3'):
#     tokenized_text = " ".join(str(model_card[field]) for field in fields if field in model_card)
#     response = ollama.embeddings(model=llm, prompt=tokenized_text)
#     return response["embedding"]



def embed_model_versioning(model_card, fields=None):
    if fields is None:
        fields = ['author', 'short_description', 'full_description', 'version', "input_type", "keywords", "category",
                  "input_data"]
    # return get_bert_embeddings(fields, model_card, bert_model, bert_tokenizer)
    # return word2vec_embedding(fields, model_card)
    # return embed_glove_versioning(model_card, fields)
    # return llama3_embedding(model_card, fields)
    return open_ai_embedding(model_card, fields)


# def word2vec_embedding(fields, model_card):
#     start_time = time.time()
#     # Load the model from disk in subsequent runs
#     model = KeyedVectors.load('./word2vec-google-news-300.bin')
#     end_time = time.time()
#     # print("Total Time: {}s".format(end_time-start_time))
#     # Select textual fields for comparison
#     if fields is None:
#         fields = ['author', 'short_description', 'full_description', 'version', "input_type", "keywords", "category",
#                   "input_data"]
#     # Tokenize and preprocess text in each field
#     tokened_text = [model_card[field].split() for field in fields]
#     embedding = []
#     for text in tokened_text:
#         text_embeddings = [model[word] for word in text if word in model]
#         if text_embeddings:
#             embedding.append(np.mean(text_embeddings, axis=0))
#         else:
#             embedding.append(np.zeros(300))
#     # Aggregate embeddings for each document
#     embedding = np.mean(embedding, axis=0)
#     return embedding


# def embed_graph_node2vec(model_card):
#     # Create a directed graph
#     graph = nx.DiGraph()
#
#     # Add nodes and edges to the graph
#     def add_nodes_and_edges(node, parent_node=None):
#         for key, value in node.items():
#             node_key = f"{parent_node}.{key}" if parent_node else key
#             graph.add_node(node_key, value=value)
#             if isinstance(value, dict):
#                 add_nodes_and_edges(value, parent_node=node_key)
#             elif isinstance(value, list):
#                 for idx, item in enumerate(value):
#                     item_key = f"{node_key}.{idx}"
#                     graph.add_node(item_key, value=item)
#                     graph.add_edge(node_key, item_key)
#             elif parent_node:
#                 graph.add_edge(parent_node, node_key)
#
#     add_nodes_and_edges(model_card)
#
#     # Generate Node2Vec embeddings with node features
#     node2vec = Node2Vec(graph, dimensions=128, walk_length=10, num_walks=100, workers=4)
#     model = node2vec.fit(window=10, min_count=1, batch_words=4)
#
#     # Aggregate node embeddings into a single representation for the entire graph
#     graph_embedding = np.mean([model.wv[node] for node in graph.nodes], axis=0)
#
#     return graph_embedding
