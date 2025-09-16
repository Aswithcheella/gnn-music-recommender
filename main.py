# main.py
import argparse
from src.data_processing import create_graph_data
from src.train import train_model

def main():
    parser = argparse.ArgumentParser(description="Run the GNN music recommender pipeline.")
    parser.add_argument('--stage', type=str, required=True, choices=['process', 'train', 'all'],
                        help="Which stage of the pipeline to run.")
    args = parser.parse_args()

    # Define paths for our new structure
    # The script now knows to look in the 'data/' directory for the JSONs
    raw_data_path = './data' 
    features_csv_path = "hf://datasets/maharshipandya/spotify-tracks-dataset/dataset.csv"
    graph_path = 'artifacts/graph_data.pt'
    artifacts_dir = 'artifacts'

    if args.stage == 'process' or args.stage == 'all':
        create_graph_data(raw_data_path, features_csv_path, output_dir=artifacts_dir)
    
    if args.stage == 'train' or args.stage == 'all':
        train_model(graph_path, output_dir=artifacts_dir)

if __name__ == '__main__':
    main()