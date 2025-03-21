import unittest
import json
import requests
from neo4j import GraphDatabase

class TestPatraAPI(unittest.TestCase):
    BASE_URL = 'http://'

    # Neo4j connection details
    NEO4J_URI = "neo4j://"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "PWD_HERE"

    def load_json(self, filename):
        with open(f'../examples/model_cards/{filename}', 'r') as file:
            return json.load(file)

    def load_datasheet_json(self, filename):
        with open(f'../examples/datasheets/{filename}', 'r') as file:
            return json.load(file)

    def test_0_upload_datasheet(self):
        datasheet_data = self.load_datasheet_json('imagenet.json')
        response = requests.post(f'{self.BASE_URL}/upload_ds', json=datasheet_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully uploaded the datasheet", response.json().get('message', ''))

    def test_1_upload_mc_new_model_card(self):

        data = self.load_json('tensorflow_titanic_MC.json')
        response = requests.post(f'{self.BASE_URL}/upload_mc', json=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully uploaded the model card", response.json().get('message', ''))

    def test_2_upload_mc_duplicate_model_card(self):

        data = self.load_json('tesorflow_adult_nn_MC.json')
        response = requests.post(f'{self.BASE_URL}/upload_mc', json=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully uploaded the model card", response.json().get('message', ''))


        duplicate_response = requests.post(f'{self.BASE_URL}/upload_mc', json=data)

        self.assertEqual(duplicate_response.status_code, 200)
        self.assertIn("Model card already exists", duplicate_response.json().get('message', ''))

    def test_3_update_mc(self):
        data = self.load_json('tesorflow_adult_nn_MC.json')
        response = requests.post(f'{self.BASE_URL}/update_mc', json=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully updated the model card", response.json().get('message', ''))

    def test_5_download_mc(self):
        model_card_id = "1b9e2ce1b376f4c2084c35f78543c591db132696d274ed924423e92fdbe6a64c"
        response = requests.get(f'{self.BASE_URL}/download_mc', params={'id': model_card_id})

        self.assertEqual(response.status_code, 200)
        self.assertIn("external_id", response.json())

    def test_6_download_url(self):
        model_id = "1b9e2ce1b376f4c2084c35f78543c591db132696d274ed924423e92fdbe6a64c-model"
        response = requests.get(f'{self.BASE_URL}/download_url', params={'model_id': model_id})

        self.assertEqual(response.status_code, 200)
        self.assertIn("download_url", response.json())

    def test_7_list_models(self):
        response = requests.get(f'{self.BASE_URL}/list')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_8_deployment_info(self):
        model_id = "1b9e2ce1b376f4c2084c35f78543c591db132696d274ed924423e92fdbe6a64c-model"

        response = requests.get(f'{self.BASE_URL}/model_deployments', params={'model_id': model_id})
        self.assertEqual(response.status_code, 200)

    def test_9_update_model_location(self):
        data = {
            "model_id": "1b9e2ce1b376f4c2084c35f78543c591db132696d274ed924423e92fdbe6a64c-model",
            "location": "http://new-location.com/model"
        }
        response = requests.post(f'{self.BASE_URL}/update_model_location', json=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Model location updated successfully", response.json().get('message', ''))


    def test_10_generate_hash_id(self):
        combined_string = "model-identifier-12345"
        response = requests.get(f'{self.BASE_URL}/get_hash_id', params={'combined_string': combined_string})

        self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        """Clean up by clearing all nodes in the Neo4j database after all tests."""
        driver = GraphDatabase.driver(cls.NEO4J_URI, auth=(cls.NEO4J_USER, cls.NEO4J_PASSWORD))
        try:
            with driver.session() as session:
                # Run query to delete all nodes and relationships
                session.run("MATCH (n) DETACH DELETE n")
                print("All nodes and relationships have been deleted from Neo4j.")
        finally:
            driver.close()


if __name__ == '__main__':
    unittest.main()

