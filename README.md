<div align="center">

<img src="docs/logo.png" alt="Patra Toolkit Logo" width="300"/>

  # Patra Knowledge Base

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Build Status](https://github.com/Data-to-Insight-Center/patra-kg/actions/workflows/ci.yml/badge.svg)](https://github.com/Data-to-Insight-Center/patra-kg/actions)

</div>

The Patra Knowledge Base is a system designed to manage and track AI/ML models, with the objective of making them more accountable and trustworthy. It's a key part of the Patra ModelCards framework, which aims to improve transparency and accountability in AI/ML models throughout their entire lifecycle. This includes the model's initial training phase, subsequent deployments, and ongoing usage, whether by the same or different individuals.

**Tag**: CI4AI, Software, PADI

## Explanation

At the heart of the Patra Knowledge Base is the concept of Model Cards. These cards are essentially detailed records that provide essential information about each AI/ML model. This information includes technical details like the model's accuracy and latency, but it goes beyond that to include non-technical aspects such as fairness, explainability, and the model's behavior in various deployment environments. This holistic approach is intended to create a comprehensive understanding of the model's strengths and weaknesses, enabling more informed decisions about its use and deployment

Key features and capabilities of the Patra ModelCards Framework include:

- **Semi-automated information capture:** Patra reduces the burden of manual documentation by automatically capturing information about model fairness, explainability, and performance in different deployment environments. This automation is facilitated by the [Model Card Toolkit](https://github.com/Data-to-Insight-Center/patra-toolkit)  , which invokes analysis tools and integrates the results directly into the Model Cards.
  
- **Graph-based knowledge representation:** Patra uses a graph database (Neo4j) to represent Model Cards and their relationships. This graph-based approach allows for efficient querying and inference, making it possible to track model evolution, identify similar models, and answer complex questions about model deployment and performance.
  
- **Provenance tracking:** Patra leverages the concepts of **forward and backward provenance** to comprehensively track the relationships between models, datasets, and deployment instances. This makes it possible to understand the lineage of models, trace their origins, and analyze their usage patterns.
  
- **Real-time deployment information:** Patra integrates with the [CKN Edge AI Framework](https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network)  to capture real-time information about model execution in edge environments. This includes data on performance, resource usage, and other relevant metrics, which can be used to optimize deployments and gain insights into model behavior in real-world settings.
  
- **Machine-actionable API:** Patra provides a **machine-actionable API** that allows intelligent systems in the edge-cloud continuum to query the knowledge base and make informed decisions about model selection. This enables automated model selection based on various criteria, including fairness, explainability, and performance metrics, further enhancing accountability and transparency.
  
- **Versioning and Similarity Analysis:** Patra infers relationships between model cards such as **"alternateOf," "revisionOf," and "transformativeUseOf"** by leveraging embedding vectors and cosine similarity comparisons. This capability is essential for tracking model evolution, identifying different versions, and understanding how models are adapted and reused over time.

By combining these capabilities, the Patra Knowledge Base provides a robust foundation for **trustworthy and accountable AI/ML model management within the edge-cloud continuum**. This framework addresses crucial aspects of transparency, provenance tracking, and performance monitoring, ultimately contributing to more responsible and reliable AI deployments.

For more information, please refer to the [Patra ModelCards paper](https://ieeexplore.ieee.org/document/10678710).

### Patra Server
The server is built using Flask and exposes a RESTful API for interaction with the Patra Knowledge Graph (KG).


| Endpoint                        | Method | Description                                                                                                            |
|---------------------------------|--------|------------------------------------------------------------------------------------------------------------------------|
| `/upload_mc`                    | POST   | Upload a model card to the Patra Knowledge Graph.                                                                      |
| `/update_mc`                    | POST   | Update an existing model card.                                                                                         |
| `/upload_ds`                    | POST   | Upload a datasheet to the Patra Knowledge Graph.                                                                       |
| `/search`                       | GET    | Full-text search for model cards.                                                                                      |
| `/download_mc`                  | GET    | Download a reconstructed model card from the Patra Knowledge Graph.                                                    |
| `/download_mc`                  | HEAD   | Retrieve the model card linkset through the header for the given model ID                                              |
| `/download_url`                 | GET    | Retrieve the download URL for a given model ID.                                                                        |
| `/list`                         | GET    | List all models in the Patra Knowledge Graph.                                                                          |
| `/model_deployments`            | GET    | Get all deployments for a given model ID.                                                                              |
| `/update_model_location`        | POST   | Update the model’s location in the graph.                                                                              |
| `/get_model_id`                 | GET    | Generates a model_id for a given author, name, and version.                                                            |
| `/get_huggingface_credentials`  | GET    | Get Hugging Face credentials for a given model ID.                                                                     |
| `/get_github_credentials`       | GET    | Get GitHub credentials for a given model ID.                                                                           |
| `/modelcard_linkset`            | GET    | Returns the modelcard linkset in the header for a given modelcard id<br/>ex: <server_url>/modelcard_linkset?id=<mc_id> |

For more information on the server endpoints, please refer to the [API documentation.](docs/patra_openapi.json)

---



## How-To Guide

### Prerequisites

#### System Requirements
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose) installed and running.
- Open network access to the following ports:
  - `7474` (Neo4j Web UI)
  - `7687` (Neo4j Bolt)
  - `5002` (REST Server)

#### Dependencies
- **Neo4j**: Version **5.21.0-community** is deployed via Docker (manual installation is not required).
- [Optional] **OpenAI API Key**: If the system needs to support Model Card similarities, you need to obtain a valid Open AI API key. Refer to the [OpenAI documentation](https://platform.openai.com) for instructions. This is disabled by default.


### 1. Set up Environment Variables

**Model Similarity (Optional)**  
To enable model similarity detection using OpenAI embeddings, set `ENABLE_MC_SIMILARITY` to `True` and provide your OpenAI API key:
```bash
export ENABLE_MC_SIMILARITY=True
export OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
```

**Hugging Face Integration (Optional)**  
To upload models and artifacts to Hugging Face, create a repository and generate an access token. Then, set the following environment variables:
```bash
export HF_HUB_USERNAME=<your-hf-username>
export HF_HUB_TOKEN=<your-hf-access-token>
```
Requires write access to the target Hugging Face repo.

**GitHub Integration (Optional)**  
To upload models and artifacts to GitHub, create a repository and generate an access token. Then, set the following environment variables:
```bash
export GH_HUB_USERNAME=<your-github-username>
export GH_HUB_TOKEN=<your-github-personal-access-token>
```
Requires `repo` scope enabled on the GitHub token.

### 2. Clone the repository and start services
```bash
git clone https://github.com/Data-to-Insight-Center/patra-kg.git
make up
```
  
The server will be running at port `5002`. To view Swagger documentation, navigate to `http://localhost:5002/swagger`.

Open [neo4j browser](http://localhost:7474/browser/) and log in with the credentials mentioned in the docker-compose file to view the model card data.   

- To shut down services, use:
    ```bash
    make down
    ```

---

## License

The **Patra Knowledge Base** is copyrighted by the **Indiana University Board of Trustees** and distributed under the **BSD 3-Clause License**. See the `LICENSE.txt` file for more details.

## Acknowledgements
This research is funded in part through the National Science Foundation under award #2112606, AI Institute for Intelligent CyberInfrastructure with Computational Learning in the Environment (ICICLE), and in part through Data to Insight Center (D2I) at Indiana University.

