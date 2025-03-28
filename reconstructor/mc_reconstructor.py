from ingester.database import GraphDB
import json


class MCReconstructor:
    """
    Re-constructs the model card from the Knowledge Graph
    """

    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password

        try:
            self.db = GraphDB(self.uri, self.user, self.password)
            print("Connected to the Neo4j database.")
        except Exception as e:
            print("Error connecting to the Neo4j database:", str(e))

    def reconstruct(self, model_card_id):
        metadata = {
            "mc_id": model_card_id,
            "ai_model_id": str(model_card_id + "-model"),
            "xai_id": str(model_card_id + "-xai"),
            "bias_id": str(model_card_id + "-bias"),
        }

        # retrieve the base model card
        mc_query = '''
            MATCH (mc:ModelCard {external_id: $mc_id})
            RETURN mc
            '''
        base_mc = self.get_result_dict(mc_query, "mc", metadata)

        if base_mc is None:
            return None

        # do not return the model embeddings
        if 'embedding' in base_mc:
            del base_mc["embedding"]

        # retrieve the ai_model information
        ai_model_query = '''
            MATCH (ai:Model {model_id: $ai_model_id})
            RETURN ai
            '''
        ai_model = self.get_result_dict(ai_model_query, "ai", metadata)
        base_mc["ai_model"] = ai_model

        # retrieve bias information if any
        bias_query = '''
            MATCH (ba:BiasAnalysis {external_id: $bias_id})
            RETURN ba
            '''
        bias_analysis = self.get_result_dict(bias_query, "ba", metadata)
        if bias_analysis is not None:
            base_mc["bias_analysis"] = bias_analysis

        # retrieve explainability information if any
        xai_query = '''
            MATCH (xai:ExplainabilityAnalysis {external_id: $xai_id})
            RETURN xai
            '''
        xai_analysis = self.get_result_dict(xai_query, "xai", metadata)
        if xai_analysis is not None:
            base_mc["xai_analysis"] = xai_analysis

        return json.dumps(base_mc, indent=4)

    def get_result_dict(self, query, type, metadata):
        response = self.db.get_result_query(query, metadata)
        if response is None:
            return None

        node = response[type]

        result_dict = {}
        if node is not None:
            for key in node.keys():
                result_dict[key] = node[key]
        else:
            return None
        return result_dict

    def search_kg(self, query):
        """
        Search the KG using embeddings.
        :param query:
        :return:
        """
        results = self.db.full_text_search(query)
        json_mcs = [
            {
                "mc_id": record["mc_id"],
                "name": record["name"],
                "version": record["version"],
                "short_description": record["short_description"],
                "score": record["score"]
            }
            for record in results
        ]
        return json_mcs

    def get_all_mcs(self):
        """
        "Get all the model cards as a list"
        """
        model_cards = self.db.get_all_modelcards()
        json_mcs = [
            {
                "mc_id": record["mc_id"],
                "name": record["name"],
                "version": record["version"],
                "short_description": record["short_description"]
            }
            for record in model_cards
        ]
        return json_mcs

    def get_model_location(self, model_id):
        """
        Get the model location as the download URL
        """
        model_info = self.db.get_model_location(model_id)

        if model_info is None:
            return None
        else:
            json_model = {
                "model_id": model_info["model_id"],
                "name": model_info["name"],
                "version": model_info["version"],
                "download_url": model_info["download_url"]
            }
            return json_model

    def get_deployments(self, model_id):
        """
        Get the deployments for a given model_id
        """
        deployment_info = self.db.get_deployments(model_id)
        if deployment_info is None:
            return None

        return deployment_info

    def set_model_location(self, model_id, location):
        """
        Update the model location
        """
        self.db.set_model_location(model_id, location)
