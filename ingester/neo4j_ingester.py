import time

from ingester.database import GraphDB
from ingester.graph_embedder import embed_model_versioning
import uuid
import numpy as np
import hashlib

class MCIngester:

    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
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
        exists, model_id = self.db.check_mc_exists(model_card)
        if exists:
            return exists, model_id

        if 'id' not in model_card:
            combined_string = model_card['name']+ ":" + model_card['version'] + ":" + model_card['author']
            hash_id = self.get_hash_id(combined_string)
            model_card['id'] = str(hash_id)

        embedding_start_time = time.time()

        version_embedding = embed_model_versioning(model_card)

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

        model_requirements = model_card["model_requirements"]
        if model_requirements is not None:
            requirements_id = base_mc_id + "-requirements"
            self.db.insert_model_requirements_metadata(base_mc_id, requirements_id, model_requirements)

        foundational_mc_id = model_card['foundational_model']
        if foundational_mc_id:
            self.db.connect_foundational_model(base_mc_id, foundational_mc_id)

        # infer versioning
        version_ingest_total_time, version_search_total_time = self.db.infer_versioning(model_card)
        version_ingest_total_time, version_search_total_time = 0, 0

        return exists,base_mc_id

    def update_mc(self, model_card):
        """
        update existing model card
        :param base_mc:
        :param bias_analysis:
        :param ai_model_metadata:
        :param xai_metadata:
        :return:
        """
        base_mc_id = self.db.check_update_mc(model_card)
        if base_mc_id:
            self.db.update_base_mc(base_mc_id, model_card)
            self.db.update_ai_model(base_mc_id, model_card['ai_model'])

            bias_analysis = model_card["bias_analysis"]
            if bias_analysis is not None:
                bias_id = base_mc_id + "-bias"
                self.db.update_bias_analysis_metadata(base_mc_id, bias_id, bias_analysis)

            xai_analysis = model_card["xai_analysis"]
            if xai_analysis is not None:
                xai_id = base_mc_id + "-xai"
                self.db.update_xai_analysis_metadata(base_mc_id, xai_id, xai_analysis)

            model_requirements = model_card["model_requirements"]
            if model_requirements is not None:
                requirements_id = base_mc_id + "-requirements"
                self.db.update_model_requirements_metadata(requirements_id, model_requirements)

        return base_mc_id

    def get_hash_id(self, combined_string):
        # Generate a unique hash using SHA-256
        id_hash = hashlib.sha256(combined_string.encode()).hexdigest()
        return id_hash

    def add_datasheet(self, datasheet):
        self.db.insert_datasheet(datasheet)

    def add_device(self, device):
        self.db.insert_device(device)

    def add_deployment(self, deployment):
        self.db.insert_deployment(deployment)

    def version_perf_test(self, model_card):
        return self.db.versioning_perf_test(model_card)