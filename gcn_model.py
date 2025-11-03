
import numpy as np
import networkx as nx

class SimpleGCN:
    def __init__(self, input_dim, hidden_dim, output_dim):
        self.W0 = np.random.randn(input_dim, hidden_dim) * 0.01
        self.W1 = np.random.randn(hidden_dim, output_dim) * 0.01

    def forward(self, G, node_features):
        # 1. Create Adjacency Matrix
        adj = nx.to_numpy_array(G)
        # Add self-loops
        adj = adj + np.eye(adj.shape[0])
        
        # 2. Normalize Adjacency Matrix
        D = np.diag(np.sum(adj, axis=1))
        D_inv_sqrt = np.linalg.inv(np.sqrt(D))
        A_hat = D_inv_sqrt @ adj @ D_inv_sqrt

        # 3. Create Node Feature Matrix
        H0 = np.zeros((len(G.nodes()), self.W0.shape[0]))
        node_list = list(G.nodes())
        for i, node in enumerate(node_list):
            if node in node_features:
                H0[i, :] = node_features[node]

        # 4. GCN Layers
        H1 = np.tanh(A_hat @ H0 @ self.W0) # Using tanh as activation
        H2 = A_hat @ H1 @ self.W1 # No activation on the final layer

        # 5. Graph Pooling (mean pooling)
        graph_embedding = np.mean(H2, axis=0)
        
        return graph_embedding
