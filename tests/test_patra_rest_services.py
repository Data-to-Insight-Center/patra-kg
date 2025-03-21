import os
import json
import unittest
from unittest.mock import patch, MagicMock
from neo4j import GraphDatabase
from server.server import app


class TestPatraAPI(unittest.TestCase):
    def setUp(self):
        # Set up Flask test client for endpoint testing.
        app.config['TESTING'] = True
        self.client = app.test_client()

    def load_json(self, filename):
        path = os.path.join(os.path.dirname(__file__), f"../examples/model_cards/{filename}")
        with open(path, "r") as file:
            return json.load(file)

    def load_datasheet_json(self, filename):
        path = os.path.join(os.path.dirname(__file__), f"../examples/datasheets/{filename}")
        with open(path, "r") as file:
            return json.load(file)

    def dummy_response(self, status_code, json_data):
        resp = MagicMock()
        resp.status_code = status_code
        resp.get_json.return_value = json_data
        return resp

    @patch("server.server.mc_ingester.add_datasheet")
    def test_upload_datasheet(self, mock_add_ds):
        datasheet_data = self.load_datasheet_json("imagenet.json")
        mock_add_ds.return_value = None
        response = self.client.post('/upload_ds', json=datasheet_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully uploaded the datasheet", response.get_json().get("message", ""))

    @patch("server.server.mc_ingester.add_mc")
    def test_upload_new_model_card(self, mock_add_mc):
        mock_add_mc.return_value = (False, "dummy_id")
        data = self.load_json("tensorflow_titanic_MC.json")
        response = self.client.post('/upload_mc', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully uploaded the model card", response.get_json().get("message", ""))

    @patch("server.server.mc_ingester.add_mc")
    def test_upload_duplicate_model_card(self, mock_add_mc):
        mock_add_mc.side_effect = [(False, "dummy_id"), (True, "dummy_id")]
        data = self.load_json("tesorflow_adult_nn_MC.json")
        response1 = self.client.post('/upload_mc', json=data)
        response2 = self.client.post('/upload_mc', json=data)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertIn("Model card already exists", response2.get_json().get("message", ""))

    @patch("server.server.mc_ingester.update_mc")
    def test_update_model_card(self, mock_update_mc):
        mock_update_mc.return_value = "dummy_id"
        data = self.load_json("tesorflow_adult_nn_MC.json")
        response = self.client.post('/update_mc', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully updated the model card", response.get_json().get("message", ""))

    @patch("server.server.mc_reconstructor.reconstruct")
    def test_download_model_card(self, mock_reconstruct):
        mock_reconstruct.return_value = {"external_id": "dummy_external_id"}
        model_card_id = "dummy_model_card_id"
        response = self.client.get('/download_mc', query_string={"id": model_card_id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("external_id", response.get_json())

    @patch("server.server.mc_reconstructor.get_model_location")
    def test_download_url(self, mock_get_location):
        mock_get_location.return_value = {"download_url": "http://dummy-download-url"}
        model_id = "dummy_model_id-model"
        response = self.client.get('/download_url', query_string={"model_id": model_id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("download_url", response.get_json())

    @patch("server.server.mc_reconstructor.get_all_mcs")
    def test_list_models(self, mock_get_all):
        mock_get_all.return_value = ["model1", "model2"]
        response = self.client.get('/list')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    @patch("server.server.mc_reconstructor.get_deployments")
    def test_deployment_info(self, mock_get_deployments):
        mock_get_deployments.return_value = {"deployments": ["dep1", "dep2"]}
        model_id = "dummy_model_id-model"
        response = self.client.get('/model_deployments', query_string={"model_id": model_id})
        self.assertEqual(response.status_code, 200)

    @patch("server.server.mc_reconstructor.set_model_location")
    def test_update_model_location(self, mock_set_location):
        data = {"model_id": "dummy_model_id-model", "location": "http://new-location.com/model"}
        response = self.client.post('/update_model_location', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Model location updated successfully", response.get_json().get("message", ""))

    @patch("server.server.mc_ingester.get_pid")
    @patch("server.server.mc_ingester.check_id_exists")
    def test_get_model_id_success(self, mock_check_id_exists, mock_get_pid):
        mock_get_pid.return_value = "dummy_pid"
        mock_check_id_exists.return_value = False
        response = self.client.get('/get_model_id', query_string={
            "author": "test",
            "name": "TestModel",
            "version": "0.1"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("dummy_pid", response.get_json().get("pid", ""))

    @patch("server.server.mc_ingester.get_pid")
    @patch("server.server.mc_ingester.check_id_exists")
    def test_get_model_id_missing_params(self, mock_check_id_exists, mock_get_pid):
        mock_get_pid.return_value = None
        response = self.client.get('/get_model_id', query_string={
            "author": "test",
            "name": "TestModel"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    @patch("server.server.os.getenv")
    def test_get_huggingface_credentials_success(self, mock_getenv):
        # Simulate environment variables for HF credentials
        mock_getenv.side_effect = lambda key: {"HF_HUB_USERNAME": "hf_user", "HF_HUB_TOKEN": "hf_token"}.get(key)
        response = self.client.get('/get_huggingface_credentials')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("username"), "hf_user")
        self.assertEqual(data.get("token"), "hf_token")

    @patch("server.server.os.getenv")
    def test_get_huggingface_credentials_failure(self, mock_getenv):
        mock_getenv.return_value = None
        response = self.client.get('/get_huggingface_credentials')
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    @patch("server.server.os.getenv")
    def test_get_github_credentials_success(self, mock_getenv):
        mock_getenv.side_effect = lambda key: {"GH_HUB_USERNAME": "gh_user", "GH_HUB_TOKEN": "gh_token"}.get(key)
        response = self.client.get('/get_github_credentials')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("username"), "gh_user")
        self.assertEqual(data.get("token"), "gh_token")

    @patch("server.server.os.getenv")
    def test_get_github_credentials_failure(self, mock_getenv):
        mock_getenv.return_value = None
        response = self.client.get('/get_github_credentials')
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    @classmethod
    @patch("neo4j.GraphDatabase.driver")
    def tearDownClass(cls, mock_driver):
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        try:
            with GraphDatabase.driver("neo4j://dummy:7687", auth=("dummy", "dummy")) as driver:
                with driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
                    print("Mock: All nodes and relationships have been deleted from Neo4j.")
        finally:
            driver.close()


if __name__ == '__main__':
    unittest.main()
