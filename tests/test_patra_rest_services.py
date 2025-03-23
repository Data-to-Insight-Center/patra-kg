import os
import json
import pytest
from _pytest.monkeypatch import MonkeyPatch
from unittest.mock import MagicMock
import requests
from neo4j import GraphDatabase

BASE_URL = "flask-server-url"


# Helper functions to load example JSON data
def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), f"../examples/model_cards/{filename}")
    with open(path, "r") as file:
        return json.load(file)


def load_datasheet_json(filename):
    path = os.path.join(os.path.dirname(__file__), f"../examples/datasheets/{filename}")
    with open(path, "r") as file:
        return json.load(file)


# Helper to create a dummy response using MagicMock
def dummy_response(status_code, json_data):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@pytest.fixture(scope="session", autouse=True)
def cleanup_neo4j():
    mp = MonkeyPatch()

    class DummySession:
        def run(self, query):
            print(f"Dummy run: {query}")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    class DummyDriver:
        def session(self):
            return DummySession()

        def close(self):
            print("Dummy driver closed")

    mp.setattr(GraphDatabase, "driver", lambda *args, **kwargs: DummyDriver())
    yield
    mp.undo()


def test_upload_datasheet_endpoint(monkeypatch):
    datasheet_data = load_datasheet_json("imagenet.json")
    dummy = dummy_response(200, {"message": "Successfully uploaded the datasheet"})
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: dummy)
    response = requests.post(f"{BASE_URL}/upload_ds", json=datasheet_data)
    assert response.status_code == 200
    assert "Successfully uploaded the datasheet" in response.json().get("message", "")


def test_upload_new_model_card_endpoint(monkeypatch):
    data = load_json("tensorflow_titanic_MC.json")
    dummy = dummy_response(200, {"message": "Successfully uploaded the model card", "model_card_id": "dummy_id"})
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: dummy)
    response = requests.post(f"{BASE_URL}/upload_mc", json=data)
    assert response.status_code == 200
    assert "Successfully uploaded the model card" in response.json().get("message", "")


def test_upload_duplicate_model_card_endpoint(monkeypatch):
    data = load_json("tesorflow_adult_nn_MC.json")
    responses = [
        dummy_response(200, {"message": "Successfully uploaded the model card", "model_card_id": "dummy_id"}),
        dummy_response(200, {"message": "Model card already exists", "model_card_id": "dummy_id"})
    ]

    def fake_post(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(requests, "post", fake_post)
    response1 = requests.post(f"{BASE_URL}/upload_mc", json=data)
    response2 = requests.post(f"{BASE_URL}/upload_mc", json=data)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert "Model card already exists" in response2.json().get("message", "")


def test_update_model_card_endpoint(monkeypatch):
    data = load_json("tesorflow_adult_nn_MC.json")
    dummy = dummy_response(200, {"message": "Successfully updated the model card", "model_card_id": "dummy_id"})
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: dummy)
    response = requests.post(f"{BASE_URL}/update_mc", json=data)
    assert response.status_code == 200
    assert "Successfully updated the model card" in response.json().get("message", "")


def test_download_model_card_endpoint(monkeypatch):
    model_card_id = "dummy_model_card_id"
    dummy = dummy_response(200, {"external_id": "dummy_external_id"})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/download_mc", params={"id": model_card_id})
    assert response.status_code == 200
    assert "external_id" in response.json()


def test_download_url_endpoint(monkeypatch):
    model_id = "dummy_model_id-model"
    dummy = dummy_response(200, {"download_url": "http://dummy-download-url"})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/download_url", params={"model_id": model_id})
    assert response.status_code == 200
    assert "download_url" in response.json()


def test_list_models_endpoint(monkeypatch):
    dummy = dummy_response(200, ["model1", "model2"])
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_deployment_info_endpoint(monkeypatch):
    model_id = "dummy_model_id-model"
    dummy = dummy_response(200, {"deployments": ["dep1", "dep2"]})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/model_deployments", params={"model_id": model_id})
    assert response.status_code == 200


def test_update_model_location_endpoint(monkeypatch):
    data = {"model_id": "dummy_model_id-model", "location": "http://new-location.com/model"}
    dummy = dummy_response(200, {"message": "Model location updated successfully"})
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: dummy)
    response = requests.post(f"{BASE_URL}/update_model_location", json=data)
    assert response.status_code == 200
    assert "Model location updated successfully" in response.json().get("message", "")


def test_generate_hash_id_endpoint(monkeypatch):
    dummy = dummy_response(201, {"pid": "dummy_pid"})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/get_model_id", params={"name": "model", "author": "author", "version": "1.0"})
    assert response.status_code == 201


def test_get_huggingface_credentials_success_endpoint(monkeypatch):
    dummy = dummy_response(200, {"username": "hf_user", "token": "hf_token"})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/get_huggingface_credentials")
    assert response.status_code == 200
    data = response.json()
    assert data.get("username") == "hf_user"
    assert data.get("token") == "hf_token"


def test_get_huggingface_credentials_failure_endpoint(monkeypatch):
    dummy = dummy_response(400, {"error": "Hugging Face credentials not set."})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/get_huggingface_credentials")
    assert response.status_code == 400
    assert "error" in response.json()


def test_get_github_credentials_success_endpoint(monkeypatch):
    dummy = dummy_response(200, {"username": "gh_user", "token": "gh_token"})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/get_github_credentials")
    assert response.status_code == 200
    data = response.json()
    assert data.get("username") == "gh_user"
    assert data.get("token") == "gh_token"


def test_get_github_credentials_failure_endpoint(monkeypatch):
    dummy = dummy_response(400, {"error": "Github credentials not set."})
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/get_github_credentials")
    assert response.status_code == 400
    assert "error" in response.json()
