# Patra Knowledge Base


The Patra Knowledge Base is a system designed to manage and track AI/ML models, with the objective of making them more accountable and trustworthy. It's a key part of the Patra ModelCards framework, which aims to improve transparency and accountability in AI/ML models throughout their entire lifecycle. This includes the model's initial training phase, subsequent deployments, and ongoing usage, whether by the same or different individuals.

At the heart of the Patra Knowledge Base is the concept of Model Cards. These cards are essentially detailed records that provide essential information about each AI/ML model. This information includes technical details like the model's accuracy and latency, but it goes beyond that to include non-technical aspects such as fairness, explainability, and the model's behavior in various deployment environments. This holistic approach is intended to create a comprehensive understanding of the model's strengths and weaknesses, enabling more informed decisions about its use and deployment

For more information, please refer to the [Patra ModelCards paper](https://arxiv.org/abs/2109.15000).

Patra Toolkit for generation of model cards can be found at the [Patra Toolkit Repository](https://github.com/Data-to-Insight-Center/patra-toolkit)

## API Endpoints
The server is built using Flask and exposes a RESTful API for interaction with the Patra Knowledge Graph (KG).


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