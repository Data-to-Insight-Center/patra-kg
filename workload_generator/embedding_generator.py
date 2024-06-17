import json
from ingester.graph_embedder import embed_model_versioning, embed_graph_node2vec, embed_glove_versioning
from parser.json_mc_parser import parse_json_mc
from sklearn.metrics.pairwise import cosine_similarity

data = parse_json_mc("../examples/model_cards/uci_cnn_mc.json")
embedding_1 = embed_model_versioning(data).reshape(1, -1)
data2 = parse_json_mc("../examples/model_cards/uci_cnn_mc_v2.json")
embedding_2 = embed_model_versioning(data2).reshape(1, -1)
data3 = parse_json_mc("../examples/model_cards/different_mc.json")
embedding_3 = embed_model_versioning(data3).reshape(1, -1)
data4 = parse_json_mc("../examples/model_cards/different_dataset_mc.json")
embedding_4 = embed_model_versioning(data4).reshape(1, -1)

data5 = parse_json_mc("../examples/model_cards/foundational_uci.json")
embedding_5 = embed_model_versioning(data4).reshape(1, -1)


print("Cosine similarity for versions: {}".format(cosine_similarity(embedding_1, embedding_2)))
print("Cosine similarity different models: {}".format(cosine_similarity(embedding_1, embedding_3)))
print("Cosine similarity different models: {}".format(cosine_similarity(embedding_1, embedding_4)))
print("Cosine similarity different models: {}".format(cosine_similarity(embedding_2, embedding_3)))
print("Cosine similarity different models: {}".format(cosine_similarity(embedding_1, embedding_5)))




