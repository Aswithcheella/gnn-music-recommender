import torch
import json
import pandas as pd
import os
from .model import Model # Use relative import within a package

class Recommender:
    """Handles loading artifacts and generating song recommendations."""
    def __init__(self, artifact_dir='artifacts'):
        # --- THIS IS THE FIX (Part 1) ---
        # Define the map location based on where the code is running
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")

        # --- Load all necessary artifacts ---
        print("Loading artifacts...")
        # Apply the map_location to the torch.load calls
        self.data = torch.load(
            os.path.join(artifact_dir, 'graph_data.pt'), 
            weights_only=False
        ).to(self.device)
        self.data['playlist'].node_id = torch.arange(self.data['playlist'].num_nodes).to(self.device)

        # (JSON loading remains the same)
        with open(os.path.join(artifact_dir, 'song_mapping.json'), 'r') as f:
            self.song_mapping = json.load(f)
        with open(os.path.join(artifact_dir, 'playlist_mapping.json'), 'r') as f:
            self.playlist_mapping = json.load(f)

        self.inv_song_mapping = {v: k for k, v in self.song_mapping.items()}
        self.enriched_df = pd.read_csv(os.path.join(artifact_dir, 'cleaned_playlists_and_tracks.csv'))

        # --- Load the trained model ---
        self.model = Model(
            hidden_channels=64,
            num_playlists=self.data['playlist'].num_nodes,
            num_song_features=self.data['song'].x.shape[1]
        ).to(self.device)
        
        # --- THIS IS THE FIX (Part 2) ---
        # Apply the map_location here as well
        self.model.load_state_dict(
            torch.load(
                os.path.join(artifact_dir, 'trained_model_weights_gpu.pt'), 
                map_location=self.device
            )
        )
        self.model.eval()

        # --- Generate final embeddings ---
        print("Generating final embeddings for all nodes...")
        with torch.no_grad():
            self.final_embeddings = self.model(self.data)
        print("Recommender ready.")

    def get_recommendations(self, playlist_id, num_recommendations=10):
        """Generates song recommendations for a given playlist ID."""
        if str(playlist_id) not in self.playlist_mapping:
            return {"error": f"Playlist ID {playlist_id} not found in the dataset."}

        # Get embeddings for all songs and the target playlist
        song_embeddings = self.final_embeddings['song']
        playlist_embeddings = self.final_embeddings['playlist']
        
        playlist_idx = self.playlist_mapping[str(playlist_id)]
        playlist_emb = playlist_embeddings[playlist_idx]

        # Calculate similarity scores
        scores = song_embeddings @ playlist_emb

        # Filter out songs already in the playlist
        songs_in_playlist = set(self.enriched_df[self.enriched_df['pid'] == playlist_id]['track_uri'].unique())
        mask = torch.ones(len(self.song_mapping), dtype=torch.bool, device=self.device)
        
        for uri in songs_in_playlist:
            if uri in self.song_mapping:
                song_idx = self.song_mapping[uri]
                mask[song_idx] = False
        
        scores[~mask] = -torch.inf

        # Get top-N recommendations
        _, top_k_indices = torch.topk(scores, k=num_recommendations)
        
        recommended_uris = [self.inv_song_mapping[idx.item()] for idx in top_k_indices]
        
        recs_df = self.enriched_df[self.enriched_df['track_uri'].isin(recommended_uris)][['track_name_x', 'artists']].drop_duplicates()
        
        return recs_df

if __name__ == '__main__':
    # This block allows you to test the script directly
    recommender = Recommender()
    example_pid = 405000
    recommendations = recommender.get_recommendations(example_pid)
    
    print(f"\n--- Recommendations for Playlist {example_pid} ---")
    print(recommendations)