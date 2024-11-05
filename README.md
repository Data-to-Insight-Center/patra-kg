# Patra Knowledge Base

The Patra Model Card toolkit is designed to simplify and accelerate the creation of AI/ML model cards by automating the addition of essential descriptive information about AI/ML models. The toolkit streamlines the integration of standardized details through a schema that captures key characteristics of AI/ML models.

With a semi-automated pipeline, the toolkit reduces the time and effort required to develop model cards by populating a set of descriptive fields independently, with no need for user input. These fields include fairness metrics and explainability information, generated via automated scanners and directly added to the model card.

The copyright to the Patra Model Card toolkit is held by the Indiana University Board of Trustees.

## Getting Started

### Prerequisites
- Ensure docker and docker-compose is installed and running on your machine.
- Ensure the following ports are available on your machine: 7474, 7687, 2181, 9092, 8083, 8502, 5002
- OpenAI API key. Refer https://platform.openai.com for more information.

### Quickstart

1. Clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network and run `make up`.
2. Configure the environment variables in the `config.env` file.
3. Start the Patra Knowledge Base by running: 
    ```bash 
    docker compose up
    ```