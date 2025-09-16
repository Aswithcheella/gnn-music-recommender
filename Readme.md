# Spotify GNN Music Recommender

## Overview

This project is an end-to-end MLOps implementation of a music recommendation system. It uses a Graph Neural Network (GNN) trained on the Spotify Million Playlist Dataset to learn embeddings for songs and playlists. The final output is a REST API that can generate song recommendations for a given playlist ID.

## Tech Stack

-   **Backend**: Python, FastAPI
-   **ML/GNN**: PyTorch, PyTorch Geometric
-   **Data Handling**: Pandas, Scikit-learn
-   **Containerization**: Docker, Docker Compose
-   **Cloud**: Boto3 for AWS S3 integration

## Project Structure

spotify_gnn_recommender/
├── artifacts/              # Stores outputs like the processed graph and model weights
├── data/                   # Stores raw input data (e.g., Spotify JSON slices)
├── scripts/
│   └── sync_s3.py          # Utility for syncing data/artifacts with S3
├── src/
│   ├── data_processing.py  # Script to process raw data and build the graph
│   ├── model.py            # GNN model class definition
│   ├── train.py            # Script to train the GNN model
│   └── inference.py        # Recommender class for generating predictions
├── app.py                  # The FastAPI application server
├── main.py                 # Orchestrator for running pipeline stages
├── Dockerfile              # Instructions to build the application container
├── docker-compose.yml      # Configuration for running the container easily
└── requirements.txt        # Python dependencies


## Setup and Installation

1.  **Clone the repository** (if it's in version control).

2.  **Create and Activate a Virtual Environment**:
    ```bash
    # Create the environment
    python -m venv venv

    # Activate on macOS/Linux
    source venv/bin/activate

    # Activate on Windows
    # .\venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    *First, install PyTorch and its related libraries for your specific system (CPU/GPU) by following the [official PyG instructions](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html).* Then, install the remaining packages:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

You can run the different stages of the ML pipeline using `main.py`.

1.  **Process Raw Data**:
    *Place the raw Spotify JSON files in the `data/` directory.*
    ```bash
    python main.py --stage process
    ```
    This will generate the `graph_data.pt` and mapping files in the `artifacts/` directory.

2.  **Train the Model**:
    ```bash
    python main.py --stage train
    ```
    This will train the GNN and save the `trained_model_weights_gpu.pt` file in `artifacts/`.

## Running the API with Docker

The easiest and most reliable way to run the application is with Docker and Docker Compose.

1.  **Build and Run the Container**:
    *Make sure Docker Desktop is running.*
    ```bash
    docker-compose up --build
    ```

2.  **Access the API**:
    The API will be available at `http://127.0.0.1:8000`. You can access the interactive documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.
