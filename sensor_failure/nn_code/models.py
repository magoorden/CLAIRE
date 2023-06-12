import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import random
import math
import torchdiffeq
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# Gaussian dropout operation 
class GaussianDropout(nn.Module):
    def __init__(self, p=0.5):
        super(GaussianDropout, self).__init__()
        if p <= 0 or p >= 1:
            raise Exception("p value should accomplish 0 < p < 1")
        self.p = p
        
    def forward(self, x):
        if self.training:
            stddev = (self.p / (1.0 - self.p))**0.5
            epsilon = torch.randn_like(x) * stddev
            return x * epsilon
        else:
            return x
        
# Swish activation function
class Swish(nn.Module):
    def __init__(self, dim=-1):
        """Swish activ bootleg from
        https://github.com/wgrathwohl/LSD/blob/master/networks.py#L299
        Args:
            dim (int, optional): input/output dimension. Defaults to -1.
        """
        super().__init__()
        if dim > 0:
            self.beta = nn.Parameter(torch.ones((dim,)))
        else:
            self.beta = torch.ones((1,))

    def forward(self, x):
        if len(x.size()) == 2:
            return x * torch.sigmoid(self.beta[None, :] * x)
        else:
            return x * torch.sigmoid(self.beta[None, :, None, None] * x)
        
        
## ODE function        
class SystemNet(nn.Module):
    def __init__(self,FEATURE_TYPE,INPUT_DIM,MODEL_TYPE):
        super(SystemNet, self).__init__()
        self.input_dim = INPUT_DIM
        self.feature_type = FEATURE_TYPE
        self.Lambda = torch.tensor(-1e-2).float()
        self.model_type = MODEL_TYPE
        
        if self.model_type == "joint":  
            self.net_w_g = nn.Sequential(
                      nn.Linear(INPUT_DIM+1,64),       
                      Swish(),
                      nn.Linear(64, 32),
                      Swish(),
                      nn.Linear(32,32),
                      GaussianDropout(0.5), 
                      Swish(),
                      nn.Linear(32,16),
                      GaussianDropout(0.2),   
                      Swish(),
                      nn.Linear(16,1)
                    )   
             ## Initialization
            for m in self.net_w_g.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0, std=0.1)
                    nn.init.constant_(m.bias, val=0)           
        else: 
            ### Function for water level 
            self.net_w = nn.Sequential(
                      nn.Linear(1,16),
                      GaussianDropout(0.5),
                      nn.ReLU(),
                      nn.Linear(16,16),
                      GaussianDropout(0.2),
                      nn.ReLU(),
                      nn.Linear(16,1),
                      nn.ReLU(),
                    )
            ### Function for gauge measurements 
            self.net_g = nn.Sequential(
                      nn.Linear(INPUT_DIM, 32),
                      GaussianDropout(0.5),     
                      nn.ReLU(),#nn.Tanh(),
                      nn.Linear(32, 8),
                      GaussianDropout(0.2), #nn.Dropout(0.5),             
                      nn.ReLU(),#Swish(),
                      nn.Linear(8,1)
                        )
            ## Initialization
            for m in self.net_w.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0, std=0.1)
                    nn.init.constant_(m.bias, val=0)

            for m in self.net_g.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0, std=0.1)
                    nn.init.constant_(m.bias, val=0)       

    @staticmethod
    def input_interp(t, input_vals):
        """Custom forward interpolating function without numpy"""
        timepoints = torch.tensor(np.arange(0, input_vals.shape[0])).float()
        assert len(input_vals) == len(timepoints)
        # Get list indicating if t <= tp fpr all tp in timepoints
        t_smaller_time = [1 if t <= tp else 0 for tp in timepoints]
        # Return value corresponding to first tp that fulfills t <= tp
        if any(t_smaller_time):
            idx_last_value = t_smaller_time.index(1)
            val_interp = input_vals[idx_last_value]
        # Return last value if there is no tp that fulfills t <= tp
        else:
            val_interp = input_vals[len(input_vals)-1]
        return val_interp

    def forward(self, t, w, g): ## ODE function
       if self.model_type == "joint": 
           w_g = torch.cat((w.reshape(-1,1),g.reshape(-1,self.input_dim)),axis=-1) 
           #print(w_g.shape)
           return self.net_w_g(w_g)
       else:
         return self.Lambda*self.net_w(w.reshape(-1,1)**2)+self.net_g(g.reshape(-1,self.input_dim))
        
## Main model
class Model():  
    def __init__(self,FEATURE_TYPE,INPUT_DIM,MODEL_TYPE,SOLVER,PATH):
        self.solver = SOLVER    
        self.system_net = SystemNet(FEATURE_TYPE,INPUT_DIM,MODEL_TYPE).to(device)
        self.system_net.load_state_dict(torch.load(PATH))
        
    def predict_(self,y0,g,step,mc_num):   
        timepoints_test = torch.arange(0,step).float()
        rhs_fun_test = lambda t, x: self.system_net.forward(t, x, self.system_net.input_interp(t, g))
        w_pred_ls = []
        for i in range(mc_num):
            with torch.no_grad():
                w_p = torchdiffeq.odeint(rhs_fun_test, y0, timepoints_test, method = self.solver).detach().numpy()
            w_pred_ls.append(w_p)
        w_pred = np.mean(np.stack(w_pred_ls),axis=0)[:,None]     
        w_std = np.std(np.stack(w_pred_ls),axis=0)[:,None]
        return w_pred, w_std
    
    
    
    