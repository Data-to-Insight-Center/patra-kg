# Patra Knowledge Base

The **Patra Model Card Toolkit** is designed to simplify and accelerate the creation of AI/ML model cards, automating the addition of essential descriptive information. This toolkit streamlines the integration of standardized details through a schema that captures key characteristics of AI/ML models, supporting transparency, accountability, and ease of use in model documentation.

The toolkit's semi-automated pipeline reduces the time and effort required to develop model cards by populating descriptive fields such as fairness metrics and explainability insights through automated scanners.

---

## Getting Started

### Prerequisites

Ensure the following requirements are met before starting:

- **Docker** and **Docker Compose** are installed and running.
- **Ports**: The following ports are available on your machine: `7474`, `7687`, `2181`, `9092`, `8083`, `8502`, `5002`.
- **OpenAI API Key**: Refer [OpenAI documentation](https://platform.openai.com) for more information.

---

## Quickstart

### Step 1: Set Up the Knowledge Graph
- If a message broker is unavailable, start one using the [CKN repository](https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network).
    ```bash
    git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network
    cd cyberinfrastructure-knowledge-network
    make up
    ```

### Step 2: Configure Environment Variables
- Set the environment variables in the `config.env` file.

### Step 3: Start the Patra Knowledge Base
- Launch the Patra Knowledge Base by running:
    ```bash
    docker compose up
    ```

---

## License

The Patra Knowledge Base toolkit is copyrighted by the Indiana University Board of Trustees and distributed under the BSD 3-Clause License. See `LICENSE.txt` for more information.

## Reference

S. Withana and B. Plale, "Patra ModelCards: AI/ML Accountability in the Edge-Cloud Continuum," *2024 IEEE 20th International Conference on e-Science (e-Science)*, Osaka, Japan, 2024, pp. 1-10, doi: 10.1109/e-Science62913.2024.10678710.
