import torch
import numpy as np
import matplotlib.pyplot as plt

def forward(x):
    return w[0]*(x**2) + w[1]*x+w[2]

def lossfunc(x,y):
    y_pred = forward(x)
    return (y-y_pred)**2

if __name__ == "__main__":
    print("success")
    w = torch.Tensor([2.0,-1.0,3.0])
    w.requires_grad = True
    x_data = [1.0,2.0,3.0,-1.0,-2.0]
    y_data = [3.0,7.0,13.0,1.0,3.0]
    for epoch in range(100):
        for x,y in zip(x_data,y_data):
            l = lossfunc(x,y)
            l.backward()
            print ('\tgrad:', x, y, w)
            w.data = w.data - 0.01* w.grad.data
            w.grad.data.zero_()
        print("progress:",epoch,l.item())
    print("perdict(after training)",4,forward(4).item())





