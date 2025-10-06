import os
import sys
from flask import Flask, request, jsonify, Response
from flask_restx import Api, Resource

CURRENT_DIR = os.path.dirname(__file__)
# Two levels up from simple/ to project root
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from reconstructor.mc_reconstructor import MCReconstructor

app = Flask(__name__)
api = Api(app, version='1.0', title='Patra API',
          description='API to interact with Patra Knowledge Graph',
          doc='/swagger')

NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PWD = "password"

mc_reconstructor = MCReconstructor(NEO4J_URI, NEO4J_USERNAME, NEO4J_PWD)

@app.route('/')
def home():
    return "Welcome to the Patra Knowledge Base", 200

@api.route('/modelcards')
class ModelCardList(Resource):
    def get(self):
        return mc_reconstructor.get_all_mcs()

@api.route('/modelcard/<string:mc_id>')
class ModelCardDetail(Resource):
    def get(self, mc_id):
        card = mc_reconstructor.reconstruct(mc_id)
        if card is None:
            return {"error": f"Model card '{mc_id}' not found"}, 404
        return card

@api.route('/modelcards/search')
class SearchModelCards(Resource):
    def get(self):
        return mc_reconstructor.search_kg(request.args.get('q'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)