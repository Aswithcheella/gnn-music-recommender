# src/model.py
import torch
# import torch_geometric.nn as pyg_nn
from torch_geometric.nn import SAGEConv, HeteroConv

class Model(torch.nn.Module):
    def __init__(self, hidden_channels, num_playlists, num_song_features):
        super().__init__()
        
        self.playlist_embed = torch.nn.Embedding(num_playlists, hidden_channels)

        self.conv1 = HeteroConv({
            ('song', 'belongs_to', 'playlist'): SAGEConv((num_song_features, hidden_channels), hidden_channels),
            ('playlist', 'contains', 'song'): SAGEConv((hidden_channels, num_song_features), hidden_channels),
        }, aggr='sum')

        self.conv2 = HeteroConv({
            ('song', 'belongs_to', 'playlist'): SAGEConv(hidden_channels, hidden_channels),
            ('playlist', 'contains', 'song'): SAGEConv(hidden_channels, hidden_channels),
        }, aggr='sum')

    def forward(self, data):
        x_dict = {
          "song": data["song"].x,
          "playlist": self.playlist_embed(data["playlist"].node_id),
        }
        x_dict = self.conv1(x_dict, data.edge_index_dict)
        x_dict = {key: x.relu() for key, x in x_dict.items()}
        x_dict = self.conv2(x_dict, data.edge_index_dict)
        return x_dict

    def decode(self, song_embedding, playlist_embedding):
        return (song_embedding * playlist_embedding).sum(dim=-1)