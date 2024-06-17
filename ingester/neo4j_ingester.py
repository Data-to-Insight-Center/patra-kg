import time

from ingester.database import GraphDB
from ingester.graph_embedder import embed_model_versioning
import uuid


class MCIngester:

    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password

        #testing DB connection
        self.test_db_connect()

    def test_db_connect(self):
        try:
            self.db = GraphDB(self.uri, self.user, self.password)
            print("Connected to the Neo4j database.")
        except Exception as e:
            print("Error connecting to the Neo4j database:", str(e))

    def add_mc(self, model_card):
        """
        Add model cards to the Knowledge Graph
        :param base_mc:
        :param bias_analysis:
        :param ai_model_metadata:
        :param xai_metadata:
        :return:
        """
        if 'id' not in model_card:
            random_uid = uuid.uuid4()
            model_card['id'] = str(random_uid)

        embedding_start_time = time.time()

        version_embedding = embed_model_versioning(model_card)

        # model_card['v_embedding'] = version_embedding
        model_card['embedding'] = version_embedding

        embedding_total_time = time.time() - embedding_start_time

        self.db.insert_base_mc(model_card)

        base_mc_id = model_card['id']
        datasheet_id = model_card['input_data']
        self.db.connect_datasheet_mc(datasheet_id, base_mc_id)
        self.db.insert_ai_model(base_mc_id, model_card['ai_model'])

        bias_analysis = model_card["bias_analysis"]
        if bias_analysis is not None:
            bias_id = base_mc_id + "-bias"
            self.db.insert_bias_analysis_metadata(base_mc_id, bias_id, bias_analysis)

        xai_analysis = model_card["xai_analysis"]
        if xai_analysis is not None:
            xai_id = base_mc_id + "-xai"
            self.db.insert_xai_analysis_metadata(base_mc_id, xai_id, xai_analysis)

        # infer versioning
        # version_ingest_total_time, version_search_total_time = self.db.infer_versioning(model_card)
        version_ingest_total_time, version_search_total_time = 0, 0

        return embedding_total_time, version_ingest_total_time, version_search_total_time

    def add_datasheet(self, datasheet):
        self.db.insert_datasheet(datasheet)

    def add_device(self, device):
        self.db.insert_device(device)

    def add_deployment(self, deployment):
        self.db.insert_deployment(deployment)

    def version_perf_test(self, model_card):
        return self.db.versioning_perf_test(model_card)