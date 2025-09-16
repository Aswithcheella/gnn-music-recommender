# src/data_processing.py
import os
import pandas as pd
import json
from tqdm import tqdm
import torch
from torch_geometric.data import HeteroData

def create_graph_data(base_path, features_path, output_dir='artifacts'):
    """Processes raw data and creates the graph object and mappings."""
    print("Starting data processing...")
    
    # --- Load and process JSON files ---
    json_files = [f for f in os.listdir(base_path) if f.endswith('.json')]
    all_dfs = []
    for file_name in tqdm(json_files, desc="Processing JSON files"):
        file_path = os.path.join(base_path, file_name)
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        playlists_df = pd.json_normalize(data['playlists'])
        tracks_df = playlists_df.explode('tracks')

        if not tracks_df.empty and 'tracks' in tracks_df.columns and tracks_df['tracks'].notna().any():
            tracks_normalized_df = pd.json_normalize(tracks_df['tracks'])
            temp_df = pd.concat([
                tracks_df[['pid', 'name']].reset_index(drop=True),
                tracks_normalized_df.reset_index(drop=True)
            ], axis=1)
            all_dfs.append(temp_df)

    final_df = pd.concat(all_dfs, ignore_index=True)

    # --- Merge with Features ---
    final_df['track_uri'] = final_df['track_uri'].str.split(':').str[-1]
    track_features_df = pd.read_csv(features_path)
    enriched_df = pd.merge(final_df, track_features_df, left_on='track_uri', right_on='track_id', how='left')
    
    # --- Clean Data ---
    cleaned_df = enriched_df.dropna()
    print(f"Data cleaned. Final number of interactions: {len(cleaned_df)}")

    # --- Build Graph ---
    print("Starting graph construction...")
    unique_track_uris = cleaned_df['track_uri'].unique()
    unique_pids = cleaned_df['pid'].unique()

    song_mapping = {uri: i for i, uri in enumerate(unique_track_uris)}
    playlist_mapping = {int(pid): i for i, pid in enumerate(unique_pids)}

    unique_songs_df = cleaned_df.drop_duplicates(subset='track_uri').sort_values('track_uri')
    feature_cols = ['danceability', 'energy', 'loudness', 'speechiness', 'acousticness',
                    'instrumentalness', 'liveness', 'valence', 'tempo', 'popularity']
    song_features = unique_songs_df[feature_cols].to_numpy()
    song_features_tensor = torch.tensor(song_features, dtype=torch.float32)

    song_indices = cleaned_df['track_uri'].map(song_mapping).to_numpy()
    playlist_indices = cleaned_df['pid'].map(playlist_mapping).to_numpy()
    edge_index = torch.tensor([song_indices, playlist_indices], dtype=torch.long)

    data = HeteroData()
    data['song'].x = song_features_tensor
    data['playlist'].num_nodes = len(unique_pids)
    data['song', 'belongs_to', 'playlist'].edge_index = edge_index
    data['playlist', 'contains', 'song'].edge_index = edge_index.flip([0])
    
    # --- Save Artifacts ---
    os.makedirs(output_dir, exist_ok=True)
    torch.save(data, os.path.join(output_dir, 'graph_data.pt'))
    with open(os.path.join(output_dir, 'song_mapping.json'), 'w') as f:
        json.dump(song_mapping, f)
    with open(os.path.join(output_dir, 'playlist_mapping.json'), 'w') as f:
        json.dump(playlist_mapping, f)
    
    # Save a copy of cleaned data for inference step
    cleaned_df.to_csv(os.path.join(output_dir, 'cleaned_playlists_and_tracks.csv'), index=False)
    
    print("Graph and mappings saved successfully to artifacts/ directory.")

if __name__ == '__main__':
    # Example paths for running directly
    base_data_path = '/kaggle/input/spotify-million-playlist'
    features_csv_path = "hf://datasets/maharshipandya/spotify-tracks-dataset/dataset.csv"
    create_graph_data(base_data_path, features_csv_path)