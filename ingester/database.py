import multiprocessing

from neo4j import GraphDatabase
import time
from scipy.spatial.distance import cosine
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from numpy.linalg import norm


def calculate_cosine(zipped_input):
    threshold = 0.90
    new_embedding, model_id, model_embedding = zipped_input
    # model_id = record['model_id']
    # model_embedding = record['model_embedding']
    # similarity = cosine(new_embedding, model_embedding)
    similarity = np.dot(new_embedding, model_embedding) / (norm(new_embedding) * norm(model_embedding))

    if similarity > threshold:
        return similarity, model_id


class GraphDB:
    _instance = None

    def __new__(cls, uri, user, password):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.driver = GraphDatabase.driver(uri, auth=(user, password))
        return cls._instance

    def close(self):
        if self.driver:
            self.driver.close()

    def check_mc_exists(self, metadata):
        with self.driver.session() as session:
            check_query = """
                      OPTIONAL MATCH (mc:ModelCard)
                      WHERE mc.name = $name AND 
                            mc.version = $version AND 
                            mc.short_description = $short_description AND 
                            mc.full_description = $full_description AND 
                            mc.keywords = $keywords AND 
                            mc.author = $author AND 
                            mc.input_data = $input_data AND 
                            mc.output_data = $output_data AND 
                            mc.input_type = $input_type AND 
                            mc.categories = $category
                      RETURN mc
                      LIMIT 1
                      """

            result = session.run(check_query, metadata)
            matched_node = result.single()

            if matched_node and matched_node.get('mc'):
                return True, matched_node.get('mc')['external_id']
            else:
               return False, None

    def check_update_mc(self, metadata):
        with self.driver.session() as session:
            check_query = """
                      OPTIONAL MATCH (mc:ModelCard)
                      WHERE mc.name = $name AND 
                            mc.version = $version AND 
                            mc.author = $author AND 
                            mc.input_data = $input_data AND 
                            mc.output_data = $output_data
                      RETURN mc
                      LIMIT 1
                      """

            result = session.run(check_query, metadata)
            matched_node = result.single()

            if matched_node and matched_node.get('mc'):
                return matched_node.get('mc')['external_id']
            else:
               return None

    def insert_base_mc(self, metadata):
        with self.driver.session() as session:
            query = """
               CREATE (mc:ModelCard {external_id: $id, name: $name, version: $version, short_description: $short_description,
                                          full_description: $full_description, keywords: $keywords, author: $author,
                                          input_data: $input_data, output_data: $output_data, input_type: $input_type,
                                          categories: $category, embedding: $embedding})
               """
            session.run(query, metadata)

    def update_base_mc(self, model_card_id, metadata):
        external_id = str(model_card_id)
        with self.driver.session() as session:
            query = """
                MATCH (mc:ModelCard {external_id: $id})
                SET mc.name = $name,
                    mc.version = $version,
                    mc.short_description = $short_description,
                    mc.full_description = $full_description,
                    mc.keywords = $keywords,
                    mc.author = $author,
                    mc.input_data = $input_data,
                    mc.output_data = $output_data,
                    mc.input_type = $input_type,
                    mc.categories = $category
            """
            session.run(query, metadata, id=external_id)

    def insert_ai_model(self, model_card_id, ai_model_metadata):
        model_id = str(model_card_id + "-model")
        with self.driver.session() as session:
            query = """
               CREATE (model:Model {model_id: $id, name: $name, version: $version, description: $description,
                                   owner: $owner, location: $location, license: $license, framework: $framework, 
                                   model_type: $model_type, test_accuracy: $test_accuracy, 
                                   foundational_model: $foundational_model})
            """
            session.run(query, ai_model_metadata, id=model_id)

            metrics = ai_model_metadata['metrics']
            for key, value in metrics.items():
                key = key.replace(" ", "_")
                query = f"""
                            MATCH (model:Model {{model_id: $model_id}})
                            SET model.{key} = $value
                            """
                session.run(query, model_id=model_id, value=value)

            query = """
                MATCH (model:Model {model_id: $model_id}), (mc:ModelCard {external_id: $mc_id})
                CREATE (model)<-[:USED]-(mc)
                """
            session.run(query, model_id=model_id, mc_id=model_card_id)

            foundational_model = ai_model_metadata['foundational_model']
            if foundational_model is not None:
                query = """
                                MATCH (mc:ModelCard {external_id: $mc_id}), (foundational_model:ModelCard {external_id: $fc_id})
                                CREATE (mc)-[:USED_BY]->(foundational_model)
                                """
                session.run(query, fc_id=foundational_model, mc_id=model_card_id)

    def update_ai_model(self, model_card_id, ai_model_metadata):
        model_id = str(model_card_id + "-model")
        with self.driver.session() as session:

            query = """
                MATCH (model:Model {model_id: $id})
                SET model.name = $name,
                    model.version = $version,
                    model.description = $description,
                    model.owner = $owner,
                    model.location = $location,
                    model.license = $license,
                    model.framework = $framework,
                    model.model_type = $model_type,
                    model.test_accuracy = $test_accuracy,
                    model.foundational_model = $foundational_model
            """

            session.run(query, ai_model_metadata, id=model_id)

            # Update the metrics properties on the model node
            metrics = ai_model_metadata['metrics']
            for key, value in metrics.items():
                key = key.replace(" ", "_")
                query = f"""
                    MATCH (model:Model {{model_id: $model_id}})
                    SET model.{key} = $value
                """
                session.run(query, model_id=model_id, value=value)

            # query = """
            #     MATCH (model:Model {model_id: $model_id}), (mc:ModelCard {external_id: $mc_id})
            #     CREATE (model)<-[:USED]-(mc)
            #     """
            # session.run(query, model_id=model_id, mc_id=model_card_id)

            # foundational_model = ai_model_metadata['foundational_model']
            # if foundational_model is not None:
            #     query = """
            #                     MATCH (mc:ModelCard {external_id: $mc_id}), (foundational_model:ModelCard {external_id: $fc_id})
            #                     CREATE (mc)-[:USED_BY]->(foundational_model)
            #                     """
            #     session.run(query, fc_id=foundational_model, mc_id=model_card_id)

    def insert_bias_analysis_metadata(self, model_card_id, bias_id, bias_analysis_metadata):
        bias_name = model_card_id + "bias_analysis"
        with self.driver.session() as session:
            query = """
            CREATE (bias_analysis:BiasAnalysis {external_id: $id, name: $name})
            """
            session.run(query, name=bias_name, id=bias_id)

            for key, value in bias_analysis_metadata.items():
                key = key.replace(" ", "_")
                query = f"""
                            MATCH (ba:BiasAnalysis {{external_id: $bias_id}})
                            SET ba.{key} = $value
                            """
                session.run(query, bias_id=bias_id, value=value)

            query = """
                    MATCH (ba:BiasAnalysis {external_id: $bias_id}), (mc:ModelCard {external_id: $mc_id})
                    CREATE (ba)<-[:BIAS_ANALYSIS]-(mc)
                    """
            session.run(query, bias_id=bias_id, mc_id=model_card_id)

    def update_bias_analysis_metadata(self, model_card_id, bias_id, bias_analysis_metadata):
        bias_name = model_card_id + "bias_analysis"
        with self.driver.session() as session:
            # MERGE to ensure the node exists or create it if not
            query = """
            MERGE (bias_analysis:BiasAnalysis {external_id: $id})
            ON CREATE SET bias_analysis.name = $name
            """
            session.run(query, name=bias_name, id=bias_id)

            # Update the bias_analysis properties from bias_analysis_metadata
            for key, value in bias_analysis_metadata.items():
                key = key.replace(" ", "_")
                query = f"""
                            MATCH (ba:BiasAnalysis {{external_id: $bias_id}})
                            SET ba.{key} = $value
                            """
                session.run(query, bias_id=bias_id, value=value)

            # query = """
            #         MATCH (ba:BiasAnalysis {external_id: $bias_id}), (mc:ModelCard {external_id: $mc_id})
            #         CREATE (ba)<-[:BIAS_ANALYSIS]-(mc)
            #         """
            # session.run(query, bias_id=bias_id, mc_id=model_card_id)

    def insert_xai_analysis_metadata(self, model_card_id, xai_id, xai_analysis_metadata):
        xai_name = model_card_id + "xai_analysis"

        with self.driver.session() as session:
            query = """
            CREATE (xai:ExplainabilityAnalysis {external_id: $id, name: $name})
            """
            session.run(query, name=xai_name, id=xai_id)

            for key, value in xai_analysis_metadata.items():
                key = key.replace(" ", "_")
                query = f"""
                            MATCH (xai:ExplainabilityAnalysis {{external_id: $bias_id}})
                            SET xai.{key} = $value
                            """
                session.run(query, bias_id=xai_id, value=value)

            query = """
                    MATCH (xai:ExplainabilityAnalysis {external_id: $xai_id}), (mc:ModelCard {external_id: $mc_id})
                    CREATE (xai)<-[:XAI_ANALYSIS]-(mc)
                    """
            session.run(query, xai_id=xai_id, mc_id=model_card_id)

    def update_xai_analysis_metadata(self, model_card_id, xai_id, xai_analysis_metadata):
        xai_name = model_card_id + "xai_analysis"

        with self.driver.session() as session:
            # Match the existing ExplainabilityAnalysis node
            query = """
            MATCH (xai:ExplainabilityAnalysis {external_id: $id})
            SET xai.name = $name
            """
            session.run(query, name=xai_name, id=xai_id)

            # Update existing node properties
            for key, value in xai_analysis_metadata.items():
                key = key.replace(" ", "_")
                query = f"""
                            MATCH (xai:ExplainabilityAnalysis {{external_id: $bias_id}})
                            SET xai.{key} = $value
                            """
                session.run(query, bias_id=xai_id, value=value)

            # query = """
            #         MATCH (xai:ExplainabilityAnalysis {external_id: $xai_id}), (mc:ModelCard {external_id: $mc_id})
            #         CREATE (xai)<-[:XAI_ANALYSIS]-(mc)
            #         """
            # session.run(query, xai_id=xai_id, mc_id=model_card_id)

    def connect_datasheet_mc(self, datasheet_id, mc_id):
        """
        Connects the datasheet and the Model Card.
        :param datasheet_id:
        :param mc_id:
        :return:
        """
        with self.driver.session() as session:
            query = """
                                MATCH (ds:Datasheet {external_id: $data_id}), (mc:ModelCard {external_id: $mc_id})
                                CREATE (mc)-[:TRAINED_ON]->(ds)
                                RETURN ds
                                LIMIT 1
                      """

            result =  session.run(query, data_id=datasheet_id, mc_id=mc_id)
            matched_node = result.single()

            if not matched_node or not matched_node.get('ds'):
                query = """
                                   MATCH (mc:ModelCard {external_id: $mc_id})
                                   CREATE (d:Datasheet {
                                       external_id: $data_id
                                   })
                                   CREATE (mc)-[:TRAINED_ON]->(d)
                               """
                session.run(query, data_id=datasheet_id, mc_id=mc_id)

    def insert_deployment(self, deployment):
        """
        Add deployment information
        :param self:
        :param device_id:
        :param model_id:
        :param deployment:
        :return:
        """
        with self.driver.session() as session:
            query = """
                       CREATE (d:Deployment {deployment_id: $id, name: $id, start_time: $start_time, end_time: $end_time, 
                       duration_minutes: $duration_minutes, deployment_environment: $deployment_environment, 
                       deployment_location: $deployment_location, power_consumption_average_watts: $power_consumption_average_watts,
                       power_consumption_peak_watts: $power_consumption_peak_watts, cpu_consumption_average_percentage: $cpu_consumption_average_percentage,
                       cpu_consumption_peak_percentage: $cpu_consumption_peak_percentage, 
                       gpu_consumption_average_percentage: $gpu_consumption_average_percentage,
                       gpu_consumption_peak_percentage: $gpu_consumption_peak_percentage,
                       requests_served: $requests_served, mean_accuracy: $mean_accuracy, mean_latency_ms: $mean_latency_ms})
                       """
            session.run(query, deployment)

        with self.driver.session() as session:
            query = """
                                    MATCH (ed:EdgeDevice {device_id: $device_id}), (dep:Deployment {deployment_id: $dept_id})
                                    CREATE (dep)-[:On_Device]->(ed)
                                    """
            session.run(query, deployment, device_id=deployment['device_id'], dept_id=deployment['id'])

            query = """
                                                MATCH (m:Model {model_id: $model_id}), (dep:Deployment {deployment_id: $depl_id})
                                                CREATE (m)-[:Deployed_On]->(dep)
                                                """
            session.run(query, deployment, model_id=deployment['model_id'], depl_id=deployment['id'])

    def insert_datasheet(self, datasheet):
        """
        Adds the datasheet information into the graph.
        :param datasheet:
        :return:
        """
        with self.driver.session() as session:
            query = """
                   CREATE (d:Datasheet {external_id: $id, name: $name, description: $description, source: $source, download_url: $download_url,
                            version: $version, license: $license, doi: $doi, target_variable: $target_variable, categories: $categories, 
                            datapoints: $datapoints, missing_values: $missing_values, attribute_types: $attribute_types})
                   """
            session.run(query, datasheet)

            additional_metadata = datasheet['additional_metadata']
            for key in additional_metadata.keys():
                value = additional_metadata[key]
                key = key.replace(" ", "_")
                query = f"""
                                            MATCH (d:Datasheet {{external_id: $data_id}})
                                            SET d.{key} = $value
                                            """
                session.run(query, data_id=datasheet["id"], value=value)

    def insert_device(self, device):
        """
        Adds the device information into the graph.
        :param device:
        :return:
        """
        with self.driver.session() as session:
            query = """
                       CREATE (d:EdgeDevice {device_id: $device_id, name: $name, description: $description})
                       """
            session.run(query, device)

            for key, value in device.items():
                if key not in ["id", "name", "description"]:
                    key = key.replace(" ", "_")
                    query = f"""
                                                MATCH (d:EdgeDevice {{device_id: $device_id}})
                                                SET d.{key} = $value
                                                """
                    session.run(query, device_id=device["device_id"], value=value)

    def infer_versioning(self, model_card, threshold=0.95, max_nodes=1000):
        """
        Compare the inserting model with the existing models for version inferencing using cosine similarity analysis
        on the NLP processed vectors
        :param model_card:
        :param threshold: threshold for similarity for it to be a version
        :return:
        """
        # query = """
        #         MATCH (mc:ModelCard)
        #         WITH mc.external_id AS model_id, mc.v_embedding AS model_embedding
        #         WHERE NOT (mc.external_id = $mc_id)
        #         MATCH (given_model:ModelCard{external_id: $mc_id})
        #         WITH model_id, model_embedding, given_model.v_embedding AS given_embedding
        #         WITH model_id, gds.similarity.cosine(model_embedding, given_embedding) AS similarity
        #         WHERE similarity > $threshold
        #         RETURN model_id, similarity
        # """
        query = """        
                        MATCH (mc:ModelCard{external_id: $mc_id})
                        WITH mc.external_id AS model_id, mc.embedding AS given_embedding
                        CALL db.index.vector.queryNodes('modelEmbeddings', $num_nodes, given_embedding) yield node, score 
                        WHERE score > $threshold
                        RETURN score, node.external_id AS model_id
                """

        version_search_start_time = time.time()
        with self.driver.session() as session:
            result = session.run(query, mc_id=model_card['id'], threshold=threshold, num_nodes=max_nodes)
            records = list(result)

        version_search_total_time = time.time() - version_search_start_time

        # version_list = []
        # model_embedding = model_card['v_embedding']
        # for record in records:
        #     rs = self.calculate_cosine(model_embedding, record)
        #     if rs is not None:
        #         version_list.append(rs)

        # with ProcessPoolExecutor() as executor:
        #     results = list(executor.map(calculate_cosine, [(model_embedding, record['model_id'], record['model_embedding']) for record in records]))

        #     # Filter out None results
        # version_list = [rs for rs in results if rs is not None]
        #
        #
        version_query = """
        MATCH (mc1:ModelCard {external_id: $mc1_id}), (mc2:ModelCard {external_id: $mc2_id})
        CREATE (mc1)-[r1:VERSION_OF {value: $similarity}]->(mc2)
        CREATE (mc2)-[r2:VERSION_OF {value: $similarity}]->(mc1)
        RETURN r1
        """
        version_ingest_start_time = time.time()

        for record in records:
            model_id = record['model_id']
            similarity = record['score']
            if model_id == model_card['id']:
                continue
            with self.driver.session() as session:
                session.run(version_query, mc1_id=model_card['id'], mc2_id=model_id, similarity=similarity)

        version_ingest_total_time = time.time() - version_ingest_start_time

        return version_ingest_total_time, version_search_total_time

    def get_all_modelcards(self, limit=1000):
        """
        Retrieve all the model cards.
        :return:
        """
        query = """
            MATCH (mc:ModelCard)
            RETURN mc.external_id as mc_id, mc.name as name, mc.version as version, 
            mc.short_description as short_description
            LIMIT $limit
        """

        records = []
        with self.driver.session() as session:
            result = session.run(query, query_embedding=query, limit=limit)
            records = list(result)
        return records

    def get_model_location(self, model_id):
        """
        Retrieve download location for a given model
        :return:
        """
        query = """
           MATCH (n:Model {model_id: $model_id}) 
           RETURN n.model_id as model_id, n.name as name, n.version as version, n.location as download_url 
        """

        record = None
        with self.driver.session() as session:
            result = session.run(query, model_id=model_id)
            record = result.single()

        return record

    def rag_search(self, embedded_query, threshold=0.80, max_nodes=5):
        """
        Searches the knowledge graph based on the embedded query using cosine similarity and returns the results.
        :param model_card:
        :param threshold: threshold for similarity for it to be a version
        :return:
        """
        query = """        
                            CALL db.index.vector.queryNodes('modelEmbeddings', $num_nodes, $query_embedding) yield node, score 
                            WHERE score > $threshold
                            RETURN score, node.external_id AS model_id
                    """

        version_search_start_time = time.time()
        records = []
        with self.driver.session() as session:
            result = session.run(query, query_embedding=embedded_query, threshold=threshold, num_nodes=max_nodes)
            records = list(result)
        return records

    def full_text_search(self, prompt, max_nodes=10):
        """
        Searches the knowledge graph using the full text indexes on Model Cards.
        :return: list of model cards
        """
        query = """        
                 CALL db.index.fulltext.queryNodes("mcFullIndex", $prompt) YIELD node, score
                RETURN node.external_id as mc_id, node.name as name, node.version as version, 
                node.short_description as short_description, score as score
                LIMIT $num_nodes
                """
        version_search_start_time = time.time()
        records = []
        with self.driver.session() as session:
            result = session.run(query, prompt=prompt, num_nodes=max_nodes)
            records = list(result)
        return records

    def versioning_perf_test(self, model_card, threshold=0.95, max_nodes=3000):
        """
        Compare the inserting model with the existing models for version inferencing using cosine similarity analysis
        on the NLP processed vectors
        :param model_card:
        :param threshold: threshold for similarity for it to be a version
        :return:
        """
        query = """
                MATCH (mc:ModelCard)
                WITH mc.external_id AS model_id, mc.v_embedding AS model_embedding
                MATCH (given_model:ModelCard{external_id: $mc_id})
                WITH model_id, model_embedding, given_model.v_embedding AS given_embedding
                WITH model_id, gds.similarity.cosine(model_embedding, given_embedding) AS similarity
                WHERE similarity > $threshold
                RETURN model_id, similarity
        """

        version_search_start_time = time.time()
        with self.driver.session() as session:
            result = session.run(query, mc_id=model_card['external_id'], threshold=threshold)
            records = list(result)

        print(records)
        version_search_total_time = time.time() - version_search_start_time

        query = """        
                MATCH (mc:ModelCard{external_id: $mc_id})
                WITH mc.external_id AS model_id, mc.embedding AS given_embedding
                CALL db.index.vector.queryNodes('embedding', $num_nodes, given_embedding) yield node, score 
                WHERE score > $threshold
                RETURN score, node.external_id AS id
        """

        version_index_start_time = time.time()
        with self.driver.session() as session:
            indexed_result = session.run(query, mc_id=model_card['external_id'], threshold=threshold,
                                         num_nodes=max_nodes)
            indexed_records = list(indexed_result)

        print(indexed_records)
        version_index_total_time = time.time() - version_index_start_time

        return version_index_total_time, version_search_total_time

    def get_result_query(self, query, parameters):
        with self.driver.session() as session:
            result = session.run(query, parameters).single()
        return result

    def get_deployments(self, model_id):
        query = """
            MATCH (m:Model {model_id: $model_id})-[:HAS_DEPLOYMENT]->(d:Deployment)
            RETURN properties(d) as deployment_info
        """
        with self.driver.session() as session:
            result = session.run(query, model_id=model_id)
            records = [record["deployment_info"] for record in result]
            return records

    def set_model_location(self, model_id, location):
        query = """
            MATCH (m:Model {model_id: $model_id})
            SET m.location = $location
        """
        with self.driver.session() as session:
            session.run(query, model_id=model_id, location=location)
