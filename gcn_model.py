
import torch
import torch.nn as nn
import torch.nn.functional as F

class SimpleGCN(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(SimpleGCN, self).__init__()
        self.gc1 = GCNLayer(input_dim, hidden_dim)
        self.gc2 = GCNLayer(hidden_dim, output_dim)
        self.output_dim = output_dim

    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = self.gc2(x, adj)
        return x

class GCNLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super(GCNLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, features, adj):
        support = torch.mm(features, self.weight)
        output = torch.spmm(adj, support)
        return output

