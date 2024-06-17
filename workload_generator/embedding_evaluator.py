from ingester.graph_embedder import embed_model_versioning
from parser.json_mc_parser import parse_json_mc
from ingester.neo4j_ingester import MCIngester
import copy
import uuid
import random
import json
import time
from datetime import datetime, timedelta
from parser.json_mc_parser import parse_json_mc
import os
import numpy as np
import csv
import pandas as pd
from sklearn.manifold import TSNE


def get_embedding_vector(file):

    mc = parse_json_mc(file)

    start_time = time.time()
    embedding_vector = embed_model_versioning(mc)
    embedding_time = time.time() - start_time

    return embedding_vector, embedding_time

def get_cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)

    norm_v1 = np.linalg.norm(vector1)
    norm_v2 = np.linalg.norm(vector2)

    return dot_product / (norm_v1 * norm_v2)

def embedding_vector_generator(original_embedding, folder_path, label="SIMILAR"):

    results = []
    files = os.listdir(folder_path)

    for file in files:
        filepath = os.path.join(folder_path, file)

        if os.path.isfile(filepath):
            embedding_vector, embedding_time = get_embedding_vector(filepath)
            cosine_similarity = get_cosine_similarity(embedding_vector, original_embedding)
            results.append([file, cosine_similarity, embedding_time, label, embedding_vector])
    return results

def reduce_dimensions(embeddings, n_components=2, perplexity=10, n_iter=1000):
    tsne = TSNE(n_components=n_components, perplexity=perplexity, n_iter=n_iter)
    return tsne.fit_transform(embeddings)

def main():
    # results_file = "../workload_generator/evaluation/results/word2vec-google_news-300.csv"
    # results_file = "../workload_generator/evaluation/results/bert-embeddings.csv"
    # results_file = "../workload_generator/evaluation/results/glove-6B-200d.csv"
    results_file = "../workload_generator/evaluation/results/openai-text-embedding-3-small_300.csv"
    # results_file = "../workload_generator/evaluation/results/llama3-embeddings.csv"

    header = ["file", "cosine_similarity", "time", "label", "embedding_vector"]

    original_mc_file = "../workload_generator/evaluation/tensorflow-ucidataset-first.json"
    original_embedding, _ = get_embedding_vector(original_mc_file)
    original_vector = [["tensorflow-ucidataset-first.json", 1, 0, "SIMILAR", original_embedding]]
    print(len(original_embedding))

    similar_mc_similarity = embedding_vector_generator(original_embedding, "../workload_generator/evaluation/similar")
    different_mc_similarity = embedding_vector_generator(original_embedding, "../workload_generator/evaluation/dissimilar", label="DIFFERENT")

    # printing the results
    for item in similar_mc_similarity:
        print("file:{}\t\t\t\t\tcosine_similarity:{}\t\t\t\t\tlabel:{}".format(item[0], item[1], item[3]))

    for item in different_mc_similarity:
        print("file:{}\t\t\t\t\tcosine_similarity:{}\t\t\t\t\tlabel:{}".format(item[0], item[1], item[3]))

    df = pd.DataFrame(original_vector + similar_mc_similarity + different_mc_similarity, columns = header)

    all_embeddings = np.stack(df['embedding_vector'].values)

    reduced_data = reduce_dimensions(all_embeddings)
    df['tsne_1'] = reduced_data[:, 0]
    df['tsne_2'] = reduced_data[:, 1]
    df.drop('embedding_vector', axis=1, inplace=True)
    df.to_csv(results_file, index=False)

    # # writing the results to file
    # with open(results_file, mode='w', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(header)
    #
    #     for row in similar_mc_similarity:
    #         writer.writerow(row)
    #
    #     for row in different_mc_similarity:
    #         writer.writerow(row)


if __name__ == "__main__":
    main()