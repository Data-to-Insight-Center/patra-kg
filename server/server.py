from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from ingester.neo4j_ingester import MCIngester
from reconstruct.mc_reconstructor import MCReconstructor

# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USERNAME = os.getenv("NEO4J_USER")
# NEO4J_PWD = os.getenv("NEO4J_PWD")

NEO4J_LOCAL = "bolt://localhost:7689"
NEO4J_USERNAME = "neo4j"
NEO4J_PWD = "rootroot"

mc_ingester = MCIngester(NEO4J_LOCAL, NEO4J_USERNAME, NEO4J_PWD)
mc_reconstructor = MCReconstructor(NEO4J_LOCAL, NEO4J_USERNAME, NEO4J_PWD)

app = Flask(__name__)

@app.route('/upload_mc', methods=['POST'])
def upload_model_card():
    """
    Upload model card to the Patra Knowledge Graph.
    :return: model_card_id
    """
    data = request.get_json()
    base_mc_id = mc_ingester.add_mc(data)
    return jsonify({"message": "Successfully uploaded the model card", "model_card_id": base_mc_id}), 200


@app.route('/upload_ds', methods=['POST'])
def upload_datasheet():
    """
    Upload datasheet to the Patra Knowledge Graph.
    """
    datasheet = request.get_json()
    mc_ingester.add_datasheet(datasheet)
    return jsonify({"message": "Successfully uploaded the datasheet"}), 200


@app.route('/download_mc', methods=['GET'])
def download_model_card():
    """
    Download a reconstructed model card from the Patra Knowledge Graph.
    """
    mc_id = request.args.get('id')
    if not mc_id:
        return jsonify({"error": "ID is required"}), 400

    # reconstruct the model card from the Patra Knowledge Graph.
    model_card = mc_reconstructor.reconstruct(str(mc_id))

    if model_card is None:
        return jsonify({"error": "Model card could not be found!"}), 400

    return model_card, 200


if __name__ == '__main__':
    app.run(debug=True)
