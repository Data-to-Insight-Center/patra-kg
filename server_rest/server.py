import os
import logging
from urllib.parse import urlparse
import uuid
import time
import csv
from datetime import datetime

from flask import Flask, request, jsonify, Response
from flask_restx import Api, Resource

from ingester.neo4j_ingester import MCIngester
from reconstructor.mc_reconstructor import MCReconstructor

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

ENABLE_MC_SIMILARITY = os.getenv("ENABLE_MC_SIMILARITY", "False").lower() == "true"
BENCHMARK = os.getenv("BENCHMARK", "False").lower() == "true"

# Benchmark CSV files
GET_MC_BENCHMARK_CSV = "/app/timings/rest/get_modelcard_benchmark.csv"
SEARCH_BENCHMARK_CSV = "/app/timings/rest/search_benchmark.csv"

mc_ingester = MCIngester(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD, ENABLE_MC_SIMILARITY)
mc_reconstructor = MCReconstructor(
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD
)

def init_benchmark_csv(csv_file, headers):
    """Initialize benchmark CSV file with headers if it doesn't exist."""
    if not BENCHMARK:
        return
    try:
        if not os.path.exists(csv_file):
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    except (PermissionError, OSError) as e:
        logging.warning(f"Cannot initialize benchmark CSV {csv_file}: {e}")

def write_benchmark_csv(csv_file, values):
    """Write benchmark timing to CSV file."""
    if not BENCHMARK:
        return
    try:
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            formatted_values = [f"{v:.2f}" if isinstance(v, float) else v for v in values]
            writer.writerow(formatted_values)
    except (PermissionError, OSError) as e:
        logging.warning(f"Cannot write to benchmark CSV {csv_file}: {e}")

# Initialize benchmark CSV files
init_benchmark_csv(GET_MC_BENCHMARK_CSV, ['latency_ms'])
init_benchmark_csv(SEARCH_BENCHMARK_CSV, ['latency_ms'])

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
api = Api(app, version='1.0', title='Patra API',
          description='API to interact with Patra Knowledge Graph',
          doc='/swagger')


@app.route('/')
def home():
    return "Welcome to the Patra Knowledge Base", 200


@api.route('/modelcard', '/upload_mc')
class ModelCard(Resource):
    def post(self):
        """
        Upload model card to the Patra Knowledge Graph.
        """
        data = request.get_json()
        exists, base_mc_id = mc_ingester.add_mc(data)
        if exists:
            return {"message": "Model card already exists", "model_card_id": base_mc_id}, 200
        return {"message": "Successfully uploaded the model card", "model_card_id": base_mc_id}, 200


@api.route('/modelcard/<string:mc_id>')
class ModelCardDetail(Resource):
    def get(self, mc_id):
        if BENCHMARK:
            start_time = time.perf_counter()
        
        model_card = mc_reconstructor.reconstruct(mc_id)
        if model_card is None:
            return {"error": "Model card could not be found!"}, 400
        
        if BENCHMARK:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            write_benchmark_csv(GET_MC_BENCHMARK_CSV, [elapsed_time])
        
        return model_card, 200

    # def head(self, mc_id):
    #     model_card = mc_reconstructor.reconstruct(mc_id)
    #     if not model_card:
    #         return {"error": f"Model card with ID '{mc_id}' could not be found!"}, 404
        
    #     headers = mc_reconstructor.get_link_headers(model_card)
    #     response = Response(response=None, status=200, mimetype='text/plain')
    #     response.headers.update(headers)
    #     return response
        
    def put(self, mc_id):
        data = request.get_json()
        base_mc_id = mc_ingester.update_mc(data)
        if base_mc_id:
            return {"message": "Successfully updated the model card", "model_card_id": base_mc_id}, 200
        return {"message": "Model card not found", "model_card_id": base_mc_id}, 200


@api.route('/datasheet', '/upload_datasheet')
class Datasheet(Resource):
    def post(self):
        """
        Upload datasheet to the Patra Knowledge Graph.
        """
        datasheet_data = request.get_json()
        mc_ingester.add_datasheet(datasheet_data)
        return {"message": "Successfully uploaded the datasheet"}, 200


@api.route('/download_mc')
class DownloadModelCard(Resource):
    @api.param('id', 'The model card ID')
    def get(self):
        """
        Download a reconstructed model card from the Patra Knowledge Graph.
        Redirects to /modelcard/<mc_id> endpoint.
        """
        mc_id = request.args.get('id')
        if not mc_id:
            return {"error": "ID is required"}, 400

        # Redirect to the main endpoint to avoid duplicate reconstruction
        return {"message": f"Use GET /modelcard/{mc_id} instead"}, 301


@api.route('/modelcards/search')
class SearchModelCards(Resource):
    def get(self):
        """
        Full text search for model cards.
        """
        query = request.args.get('q')
        if not query:
            return {"error": "Query (q) is required"}, 400
        
        if BENCHMARK:
            start_time = time.perf_counter()
        
        results = mc_reconstructor.search_kg(query)
        
        if BENCHMARK:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            write_benchmark_csv(SEARCH_BENCHMARK_CSV, [elapsed_time])
        
        return results, 200


@api.route('/modelcard/<string:mc_id>/download_url', '/download_url/<string:mc_id>', '/get_model_location/<string:mc_id>')
class ModelDownloadURL(Resource):
    def get(self, mc_id):
        """
        Download url for a given model id.
        """
        model = mc_reconstructor.get_model_location(mc_id)
        if model is None:
            return {"error": "Model could not be found!"}, 400
        return model, 200


@api.route('/modelcards', '/list')
class ListModelCards(Resource):
    def get(self):
        """
        Lists all the models in Patra KG.
        """
        model_card_dict = mc_reconstructor.get_all_mcs()
        return model_card_dict, 200


@api.route('/modelcard/<string:mc_id>/deployments', '/model_deployments/<string:mc_id>')
class ModelDeployments(Resource):
    def get(self, mc_id):
        """
        Get all deployments for a given model ID.
        """
        deployments = mc_reconstructor.get_deployments(mc_id)
        if deployments is None:
            return {"error": "Deployments not found!"}, 400
        return deployments, 200


@api.route('/modelcard/<string:mc_id>/location', '/update_model_location/<string:mc_id>')
class UpdateModelLocation(Resource):
    def put(self, mc_id):
        """
        Update the model location.
        Expects a JSON payload.
        """
        data = request.get_json()
        if data is None:
            return {"error": "Invalid JSON payload"}, 400
        location = data.get('location')
        if not location:
            return {"error": "Location is required"}, 400
        parsed_url = urlparse(location)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return {"error": "Location must be a valid URL"}, 400
        mc_reconstructor.set_model_location(mc_id, location)
        return {"message": "Model location updated successfully"}, 200


@api.route('/credentials/huggingface')
class HFcredentials(Resource):
    def get(self):
        """
        Retrieves Hugging Face credentials.
        """
        hf_username = os.getenv("HF_HUB_USERNAME")
        hf_token = os.getenv("HF_HUB_TOKEN")
        if not hf_username or not hf_token:
            return {"error": "Hugging Face credentials not set."}, 400
        return {"username": hf_username, "token": hf_token}, 200


@api.route('/credentials/github')
class GHcredentials(Resource):
    def get(self):
        """
        Retrieves Github credentials.
        """
        gh_username = os.getenv("GH_HUB_USERNAME")
        gh_token = os.getenv("GH_HUB_TOKEN")
        if not gh_username or not gh_token:
            return {"error": "Github credentials not set."}, 400
        return {"username": gh_username, "token": gh_token}, 200


@api.route('/modelcard/<string:mc_id>/linkset')
class ModelCardLinkset(Resource):
    def get(self, mc_id):
        """
        Provides linkset relations for a model card in the HTTP Link header.
        """
        model_card = mc_reconstructor.reconstruct(mc_id)
        if not model_card:
            return {"error": f"Model card with ID '{mc_id}' could not be found!"}, 404
        
        headers = mc_reconstructor.get_link_headers(model_card)
        response = Response(response=None, status=200, mimetype='text/plain')
        response.headers.update(headers)
        return response


@api.route('/device')
class Device(Resource):
    def post(self):
        """
        Register a new edge device for deployment tracking.
        """
        data = request.get_json()
        if not data or 'device_id' not in data:
            return {"error": "device_id is required"}, 400
            
        if mc_ingester.check_device_exists(data['device_id']):
            return {"error": "Device with this ID already exists"}, 409
            
        try:
            mc_ingester.add_device(data)
            return {"message": "Device registered successfully"}, 201
        except Exception as e:
            logging.error(f"Failed to register device: {str(e)}")
            return {"error": f"Failed to register device: {str(e)}"}, 500


@api.route('/user')
class User(Resource):
    def post(self):
        """
        Register a new user for experiment tracking and model submissions.
        """
        data = request.get_json()
        if not data or 'user_id' not in data:
            return {"error": "user_id is required"}, 400
            
        if mc_ingester.check_user_exists(data['user_id']):
            return {"error": "User with this ID already exists"}, 409
            
        try:
            mc_ingester.add_user(data)
            return {"message": "User registered successfully"}, 201
        except Exception as e:
            logging.error(f"Failed to register user: {str(e)}")
            return {"error": f"Failed to register user: {str(e)}"}, 500
            

@api.route('/modelcard/id')
class GeneratePID(Resource):
    def post(self):
        """
        Generates a unique model_id.
        """
        return {"pid": str(uuid.uuid4())}, 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
