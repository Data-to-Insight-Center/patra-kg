import os
import logging
from urllib.parse import urlparse

from flask import Flask, request, jsonify, Response
from flask_restx import Api, Resource

from ingester.neo4j_ingester import MCIngester
from reconstructor.mc_reconstructor import MCReconstructor

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PWD")

ENABLE_MC_SIMILARITY = os.getenv("ENABLE_MC_SIMILARITY", "False").lower() == "true"

mc_ingester = MCIngester(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD, ENABLE_MC_SIMILARITY)
mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
api = Api(app, version='1.0', title='Patra API',
          description='API to interact with Patra Knowledge Graph',
          doc='/swagger')


@app.route('/')
def home():
    return "Welcome to the Patra Knowledge Base", 200


@api.route('/upload_mc')
class UploadModelCard(Resource):
    def post(self):
        """
        Upload model card to the Patra Knowledge Graph.
        Expects a JSON payload.
        """
        data = request.get_json()
        exists, base_mc_id = mc_ingester.add_mc(data)
        if exists:
            return {"message": "Model card already exists", "model_card_id": base_mc_id}, 200
        return {"message": "Successfully uploaded the model card", "model_card_id": base_mc_id}, 200


@api.route('/update_mc')
class UpdateModelCard(Resource):
    def post(self):
        """
        Update the existing model card.
        Expects a JSON payload.
        """
        data = request.get_json()
        base_mc_id = mc_ingester.update_mc(data)
        if base_mc_id:
            return {"message": "Successfully updated the model card", "model_card_id": base_mc_id}, 200
        return {"message": "Model card not found", "model_card_id": base_mc_id}, 200


@api.route('/upload_ds')
class UploadDatasheet(Resource):
    def post(self):
        """
        Upload datasheet to the Patra Knowledge Graph.
        Expects a JSON payload.
        """
        datasheet_data = request.get_json()
        mc_ingester.add_datasheet(datasheet_data)
        return {"message": "Successfully uploaded the datasheet"}, 200


@api.route('/search')
class SearchKG(Resource):
    @api.param('q', 'The search query')
    def get(self):
        """
        Full text search for model cards.
        """
        query = request.args.get('q')
        if not query:
            return {"error": "Query (q) is required"}, 400

        results = mc_reconstructor.search_kg(query)
        return results, 200


@api.route('/download_mc')
class DownloadModelCard(Resource):
    @api.param('id', 'The model card ID')
    def get(self):
        """
        Download a reconstructed model card from the Patra Knowledge Graph.
        """
        mc_id = request.args.get('id')
        if not mc_id:
            return {"error": "ID is required"}, 400

        model_card = mc_reconstructor.reconstruct(str(mc_id))

        if model_card is None:
            return {"error": "Model card could not be found!"}, 400

        return model_card, 200

    @api.param('id', 'The model card ID')
    def head(self):
        """
        Provides linkset relations for a model card in the HTTP Link header.
        Returns an empty body with link information in the header.
        """
        mc_id = request.args.get('id')
        if not mc_id:
            return {"error": "ID is required"}, 400

        model_card = mc_reconstructor.reconstruct(str(mc_id))

        if not model_card:
            error_payload = jsonify({"error": f"Model card with ID '{mc_id}' could not be found!"})
            return Response(response=error_payload.get_data(as_text=True), status=404, mimetype='application/json')

        generated_headers = mc_reconstructor.get_link_headers(model_card)

        # Creating the response with an empty body
        response = Response(
            response=None,
            status=200,
            mimetype='text/plain'
        )

        # Add generated headers to the response
        response.headers.update(generated_headers)
        return response


@api.route('/download_url')
class ModelDownloadURL(Resource):
    @api.param('model_id', 'The model ID')
    def get(self):
        """
        Download url for a given model id.
        """
        model_id = request.args.get('model_id')
        if not model_id:
            return {"error": "Model ID is required"}, 400

        # get the model information
        model = mc_reconstructor.get_model_location(str(model_id))

        if model is None:
            return {"error": "Model could not be found!"}, 400

        return model, 200


@api.route('/list')
class ListModels(Resource):
    def get(self):
        """
        Lists all the models in Patra KG.
        """
        model_card_dict = mc_reconstructor.get_all_mcs()
        return model_card_dict, 200


@api.route('/model_deployments')
class DeploymentInfo(Resource):
    @api.param('model_id', 'The model ID')
    def get(self):
        """
        Get all deployments for a given model ID.
        """
        model_id = request.args.get('model_id')
        if not model_id:
            return {"error": "Model ID is required"}, 400

        deployments = mc_reconstructor.get_deployments(model_id)

        if deployments is None:
            return {"error": "Deployments not found!"}, 400

        return deployments, 200


@api.route('/update_model_location')
class UpdateModelLocation(Resource):
    def post(self):
        """
        Update the model location.
        Expects a JSON payload.
        """
        data = request.get_json()
        if data is None:
            return {"error": "Invalid JSON payload"}, 400
        model_id = data.get('model_id')
        location = data.get('location')

        if not model_id or not location:
            return {"error": "Model ID and Location are required"}, 400

        parsed_url = urlparse(location)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return {"error": "Location must be a valid URL"}, 400

        mc_reconstructor.set_model_location(model_id, location)
        return {"message": "Model location updated successfully"}, 200


@api.route('/get_model_id')
class GeneratePID(Resource):
    @api.param('name', 'Model name')
    @api.param('author', 'Model author')
    @api.param('version', 'Model version')
    def get(self):
        """
        Generates a model_id for a given author, name, and version.
        Returns:
            201: New PID for that combination
            409: PID already exists; user must update version
            400: Missing parameters
        """
        author = request.headers.get("Tapis-Trusted-Username-Header", None)
        if author is None:
            author = request.args.get('author')
        name = request.args.get('name')
        version = request.args.get('version')

        if not all([author, name, version]):
            logging.error("Missing one or more required parameters: author, name, version")
            return {"error": "Author, name, and version are required"}, 400

        pid = mc_ingester.get_pid(author, name, version)
        if pid is None:
            logging.error("PID generation failed. Could not generate a unique identifier.")
            return {"error": "PID could not be generated. Please try again."}, 500

        if mc_ingester.check_id_exists(pid):
            logging.warning(f"Model ID '{pid}' already exists.")
            return {"pid": pid}, 409

        logging.info(f"Model ID successfully generated: {pid}")
        return {"pid": pid}, 201


@api.route('/get_huggingface_credentials')
class HFcredentials(Resource):
    def get(self):
        """
        Retrieves Hugging Face credentials.
        Returns a JSON object with 'username' and 'token'.
        """
        hf_username = os.getenv("HF_HUB_USERNAME")
        hf_token = os.getenv("HF_HUB_TOKEN")
        if not hf_username or not hf_token:
            return {"error": "Hugging Face credentials not set."}, 400
        return {"username": hf_username, "token": hf_token}, 200


@api.route('/get_github_credentials')
class GHcredentials(Resource):
    def get(self):
        """
        Retrieves Github credentials.
        Returns a JSON object with 'username' and 'token'.
        """
        gh_username = os.getenv("GH_HUB_USERNAME")
        gh_token = os.getenv("GH_HUB_TOKEN")
        if not gh_username or not gh_token:
            return {"error": "Github credentials not set."}, 400
        return {"username": gh_username, "token": gh_token}, 200


@api.route('/modelcard_linkset')
class ModelCardLinkset(Resource):
    @api.param('id', 'The model card ID')
    def get(self):
        """
        Provides linkset relations for a model card in the HTTP Link header.
        Returns an empty body with link information in the header.
        """
        mc_id = request.args.get('id')
        if not mc_id:
            return {"error": "ID is required"}, 400

        model_card = mc_reconstructor.reconstruct(str(mc_id))

        if not model_card:
             error_payload = jsonify({"error": f"Model card with ID '{mc_id}' could not be found!"})
             return Response(response=error_payload.get_data(as_text=True), status=404, mimetype='application/json')

        generated_headers = mc_reconstructor.get_link_headers(model_card)

        # Creating the response with an empty body
        response = Response(
            response=None,
            status=200,
            mimetype='text/plain'
        )

        # Add generated headers to the response
        response.headers.update(generated_headers)
        return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
