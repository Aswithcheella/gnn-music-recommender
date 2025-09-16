# src/train.py
import torch
import torch.nn.functional as F
import torch_geometric.transforms as T
from sklearn.metrics import roc_auc_score
import time
import os

from model import Model # Import the model class

def train_model(data_path, epochs=300, hidden_channels=64, lr=0.01, output_dir='artifacts'):
    """Loads graph data, trains the GNN model, and saves the weights."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    data = torch.load(data_path, weights_only=False)
    data['playlist'].node_id = torch.arange(data['playlist'].num_nodes)
    
    transform = T.RandomLinkSplit(...) # Same as in notebook
    train_data, val_data, test_data = transform(data)
    train_data, val_data, test_data = train_data.to(device), val_data.to(device), test_data.to(device)

    model = Model(
        hidden_channels=hidden_channels, 
        num_playlists=data['playlist'].num_nodes,
        num_song_features=data['song'].x.shape[1]
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # --- 5. Train and Test Functions (no changes needed) ---
    def train():
        model.train()
        optimizer.zero_grad()
        embeddings = model(train_data)
        
        edge_label_index = train_data['song', 'belongs_to', 'playlist'].edge_label_index
        edge_label = train_data['song', 'belongs_to', 'playlist'].edge_label
        
        pred = model.decode(
            embeddings['song'][edge_label_index[0]],
            embeddings['playlist'][edge_label_index[1]]
        )
        
        loss = F.binary_cross_entropy_with_logits(pred, edge_label)
        loss.backward()
        optimizer.step()
        return loss

    @torch.no_grad()
    def test(data_split):
        model.eval()
        embeddings = model(data_split)
        
        edge_label_index = data_split['song', 'belongs_to', 'playlist'].edge_label_index
        edge_label = data_split['song', 'belongs_to', 'playlist'].edge_label
        
        pred = model.decode(
            embeddings['song'][edge_label_index[0]],
            embeddings['playlist'][edge_label_index[1]]
        ).sigmoid()
        
        # Move predictions and labels to CPU for scikit-learn
        return roc_auc_score(edge_label.cpu().numpy(), pred.cpu().numpy())
    
    print(f"\nStarting training for {epochs} epochs...")
    for epoch in range(1, epochs + 1):
        loss = train(model, optimizer, train_data)
        val_auc = test(model, val_data)
        test_auc = test(model, test_data)
        print(f'Epoch: {epoch:03d}, Loss: {loss:.4f}, Val AUC: {val_auc:.4f}, Test AUC: {test_auc:.4f}')

    print("\nTraining complete!")
    torch.save(model.state_dict(), os.path.join(output_dir, 'trained_model_weights_gpu.pt'))
    print("Trained model weights saved.")

if __name__ == '__main__':
    graph_path = 'artifacts/graph_data.pt'
    train_model(graph_path)