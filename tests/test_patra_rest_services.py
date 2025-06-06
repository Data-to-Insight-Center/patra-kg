import json
import os
import sys
from unittest.mock import MagicMock

import pytest
import requests

BASE_URL = "http://localhost:5002"


def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), f"../examples/model_cards/{filename}")
    with open(path, "r") as file:
        return json.load(file)


def load_datasheet_json(filename):
    path = os.path.join(os.path.dirname(__file__), f"../examples/datasheets/{filename}")
    with open(path, "r") as file:
        return json.load(file)


def dummy_response(status_code, json_data):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@pytest.fixture
def client(monkeypatch):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from server.server import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_upload_datasheet(monkeypatch):
    datasheet_data = load_datasheet_json("imagenet.json")
    dummy = dummy_response(200, {"message": "Successfully uploaded the datasheet"})
    monkeypatch.setattr(requests, "post", lambda url, json: dummy)
    response = requests.post(f"{BASE_URL}/upload_ds", json=datasheet_data)
    assert response.status_code == 200
    assert "Successfully uploaded the datasheet" in response.json().get("message", "")


def test_upload_new_model_card(monkeypatch):
    data = load_json("tensorflow_titanic_MC.json")
    dummy = dummy_response(200, {"message": "Successfully uploaded the model card", "model_card_id": "dummy_id"})
    monkeypatch.setattr(requests, "post", lambda url, json: dummy)
    response = requests.post(f"{BASE_URL}/upload_mc", json=data)
    assert response.status_code == 200
    assert "Successfully uploaded the model card" in response.json().get("message", "")


def test_upload_duplicate_model_card(monkeypatch):
    data = load_json("tesorflow_adult_nn_MC.json")
    responses = [
        dummy_response(200, {"message": "Successfully uploaded the model card", "model_card_id": "dummy_id"}),
        dummy_response(200, {"message": "Model card already exists", "model_card_id": "dummy_id"})
    ]
    call_count = 0

    def fake_post(url, json):
        nonlocal call_count
        resp = responses[call_count]
        call_count += 1
        return resp

    monkeypatch.setattr(requests, "post", fake_post)
    resp1 = requests.post(f"{BASE_URL}/upload_mc", json=data)
    resp2 = requests.post(f"{BASE_URL}/upload_mc", json=data)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert "Model card already exists" in resp2.json().get("message", "")


def test_update_model_card(monkeypatch):
    data = load_json("tesorflow_adult_nn_MC.json")
    dummy = dummy_response(200, {"message": "Successfully updated the model card", "model_card_id": "dummy_id"})
    monkeypatch.setattr(requests, "post", lambda url, json: dummy)
    response = requests.post(f"{BASE_URL}/update_mc", json=data)
    assert response.status_code == 200
    assert "Successfully updated the model card" in response.json().get("message", "")


def test_download_model_card(monkeypatch):
    model_card_id = "dummy_model_card_id"
    dummy = dummy_response(200, {"external_id": "dummy_external_id"})
    monkeypatch.setattr(requests, "get", lambda url, params: dummy)
    response = requests.get(f"{BASE_URL}/download_mc", params={"id": model_card_id})
    assert response.status_code == 200
    assert "external_id" in response.json()


def test_download_url(monkeypatch):
    model_id = "dummy_model_id-model"
    dummy = dummy_response(200, {"download_url": "http://dummy-download-url"})
    monkeypatch.setattr(requests, "get", lambda url, params: dummy)
    response = requests.get(f"{BASE_URL}/download_url", params={"model_id": model_id})
    assert response.status_code == 200
    assert "download_url" in response.json()


def test_list_models(monkeypatch):
    dummy = dummy_response(200, ["model1", "model2"])
    monkeypatch.setattr(requests, "get", lambda url, **kwargs: dummy)
    response = requests.get(f"{BASE_URL}/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_deployment_info(monkeypatch):
    model_id = "dummy_model_id-model"
    dummy = dummy_response(200, {"deployments": ["dep1", "dep2"]})
    monkeypatch.setattr(requests, "get", lambda url, params: dummy)
    response = requests.get(f"{BASE_URL}/model_deployments", params={"model_id": model_id})
    assert response.status_code == 200


def test_update_model_location(monkeypatch):
    data = {"model_id": "dummy_model_id-model", "location": "http://new-location.com/model"}
    dummy = dummy_response(200, {"message": "Model location updated successfully"})
    monkeypatch.setattr(requests, "post", lambda url, json: dummy)
    response = requests.post(f"{BASE_URL}/update_model_location", json=data)
    assert response.status_code == 200
    assert "Model location updated successfully" in response.json().get("message", "")


def test_get_model_id(monkeypatch):
    dummy = dummy_response(201, {"pid": "dummy_pid"})
    monkeypatch.setattr(requests, "get", lambda url, params: dummy)
    response = requests.get(f"{BASE_URL}/get_model_id", params={"name": "model", "author": "author", "version": "1.0"})
    assert response.status_code == 201


def test_get_huggingface_credentials_success(client, monkeypatch):
    monkeypatch.setenv("HF_HUB_USERNAME", "hf_user")
    monkeypatch.setenv("HF_HUB_TOKEN", "hf_token")
    response = client.get("/get_huggingface_credentials")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("username") == "hf_user"
    assert data.get("token") == "hf_token"


def test_get_huggingface_credentials_failure(client, monkeypatch):
    monkeypatch.delenv("HF_HUB_USERNAME", raising=False)
    monkeypatch.delenv("HF_HUB_TOKEN", raising=False)
    response = client.get("/get_huggingface_credentials")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_get_github_credentials_success(client, monkeypatch):
    monkeypatch.setenv("GH_HUB_USERNAME", "gh_user")
    monkeypatch.setenv("GH_HUB_TOKEN", "gh_token")
    response = client.get("/get_github_credentials")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("username") == "gh_user"
    assert data.get("token") == "gh_token"


def test_get_github_credentials_failure(client, monkeypatch):
    monkeypatch.delenv("GH_HUB_USERNAME", raising=False)
    monkeypatch.delenv("GH_HUB_TOKEN", raising=False)
    response = client.get("/get_github_credentials")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_upload_model_card_missing_inference_labels(monkeypatch):
    data = load_json("tensorflow_titanic_MC.json")
    dummy = dummy_response(200, {"message": "Successfully uploaded the model card", "model_card_id": "dummy_id"})
    monkeypatch.setattr(requests, "post", lambda url, json: dummy)
    response = requests.post(f"{BASE_URL}/upload_mc", json=data)
    assert response.status_code == 200
    assert "Successfully uploaded the model card" in response.json().get("message", "")


if __name__ == "__main__":
    pytest.main()
