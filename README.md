# Patra Knowledge Base

The **Patra Knowledge Base** is designed to simplify and accelerate the creation of AI/ML model cards, automating the addition of essential descriptive information. This toolkit streamlines the integration of standardized details through a schema that captures key characteristics of AI/ML models, supporting transparency, accountability, and ease of use in model documentation.

The toolkit's semi-automated pipeline reduces the time and effort required to develop model cards by populating descriptive fields such as fairness metrics and explainability insights through automated scanners.

The server for the Patra Knowledge Base is built using Flask to provide a RESTful API for interacting with the Patra Knowledge Graph. 

| Endpoint                 | Method | Description                                                   |
|--------------------------|--------|---------------------------------------------------------------|
| `/upload_mc`             | POST   | Upload model card to the Patra Knowledge Graph.               |
| `/update_mc`             | POST   | Update the existing model card.                               |
| `/upload_ds`             | POST   | Upload datasheet to the Patra Knowledge Graph.                |
| `/search`                | GET    | Full text search for model cards.                             |
| `/download_mc`           | GET    | Download a reconstructed model card from the Patra Knowledge Graph. |
| `/download_url`          | GET    | Download URL for a given model ID.                            |
| `/list`                  | GET    | Lists all the models in Patra KG.                             |
| `/model_deployments`     | GET    | Get all deployments for a given model ID.                     |
| `/update_model_location` | POST   | Update the model location.                                    |
| `/get_hash_id`           | GET    | Return a unique hash for the provided combined string.        |

---

## Getting Started

### Prerequisites

Ensure the following requirements are met before starting:

- **Docker** and **Docker Compose** are installed and running.
- **Ports**: The following ports are available on your machine: `7474`, `7687`, `2181`, `9092`, `8083`, `8502`, `5002`.
- **OpenAI API Key**: Refer [OpenAI documentation](https://platform.openai.com) for more information.

---

## Quickstart

### Step 1: Configure Environment Variables
- Set OpenAI API key using the following command:
    ```bash
    export OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
    ```

- Set the Neo4j credentials if available:
    ```bash
    export neo4j_user=<NEO4J_USER>
    export neo4j_password=<NEO4J_PASSWORD>
    export neo4j_uri=<NEO4J_URI>
    ```
  Else, start the Neo4j database using:
    ```bash
    make kg
    ```

### Step 2: Start the Patra Knowledge Base
- Launch the Patra Knowledge Base by running:
    ```bash
    docker compose up
    ```

---

## License

The Patra Knowledge Base toolkit is copyrighted by the Indiana University Board of Trustees and distributed under the BSD 3-Clause License. See `LICENSE.txt` for more information.

## Reference

S. Withana and B. Plale, "Patra ModelCards: AI/ML Accountability in the Edge-Cloud Continuum," *2024 IEEE 20th International Conference on e-Science (e-Science)*, Osaka, Japan, 2024, pp. 1-10, doi: 10.1109/e-Science62913.2024.10678710.
