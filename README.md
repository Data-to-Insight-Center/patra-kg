# Patra Knowledge Base

The **Patra Knowledge Base** simplifies and accelerates the creation of AI/ML model cards by automating the integration of essential model details. It streamlines the process of documenting key characteristics of AI/ML models, enhancing transparency, accountability, and usability in model documentation.

By leveraging a semi-automated pipeline, this toolkit reduces the time and effort required to generate model cards. Descriptive fields such as fairness metrics, explainability insights, and more are populated automatically through scanners.

The server is built using Flask and exposes a RESTful API for interaction with the **Patra Knowledge Graph** (KG).

## API Endpoints

| Endpoint                 | Method | Description                                                   |
|--------------------------|--------|---------------------------------------------------------------|
| `/upload_mc`             | POST   | Upload a model card to the Patra Knowledge Graph.             |
| `/update_mc`             | POST   | Update an existing model card.                                |
| `/upload_ds`             | POST   | Upload a datasheet to the Patra Knowledge Graph.              |
| `/search`                | GET    | Full-text search for model cards.                             |
| `/download_mc`           | GET    | Download a reconstructed model card from the Patra Knowledge Graph. |
| `/download_url`          | GET    | Retrieve the download URL for a given model ID.              |
| `/list`                  | GET    | List all models in the Patra Knowledge Graph.                 |
| `/model_deployments`     | GET    | Get all deployments for a given model ID.                     |
| `/update_model_location` | POST   | Update the model’s location in the graph.                     |
| `/get_hash_id`           | GET    | Return a unique hash ID for the provided combined string.     |

---

## Getting Started

### Prerequisites

Before starting, make sure the following are in place:

- **Docker** and **Docker Compose** are installed and running on your machine.
- Ensure that the following ports are available: `7474` (Neo4j Web UI), `7687` (Neo4j Bolt), `5002` (REST Server).
- An **OpenAI API Key** is required. Refer to the [OpenAI documentation](https://platform.openai.com) for instructions.

---

## Quickstart

### Set up Environment Variables
- Set your OpenAI API key using the following command:
    ```bash
    export OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
    ```

### Launch the Patra Knowledge Base
- Start the Patra Knowledge Base using Docker Compose:
    ```bash
    make up
    ```

   Once the containers are up, you can view the ingested model cards in the [Neo4j Browser](http://localhost:7474/browser/).
   - Login with the username `neo4j` and the password `PWD_HERE`.
   - Run the following query to view the model data:
     ```cypher
     MATCH (n) RETURN n
     ```

- To stop and remove all running containers, use:
    ```bash
    make down
    ```

---

## License

The **Patra Knowledge Base** toolkit is copyrighted by the **Indiana University Board of Trustees** and distributed under the **BSD 3-Clause License**. See the `LICENSE.txt` file for more details.

## Reference

S. Withana and B. Plale, "Patra ModelCards: AI/ML Accountability in the Edge-Cloud Continuum," *2024 IEEE 20th International Conference on e-Science (e-Science)*, Osaka, Japan, 2024, pp. 1-10, doi: 10.1109/e-Science62913.2024.10678710.