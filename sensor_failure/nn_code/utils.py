import numpy as np
import torch
class DATA_LOADER():
     def __init__(self,x,y,samp_rate=6,feat_type = "hist",hist_step=3,time_delay=3):
         self.x = x # gauge value  
         self.y = y # water level 
         #self.IDX_START = IDX_START #[50,150,250,350,450] 
         self.samp_rate = samp_rate
         self.feat_type = feat_type
         #self.TRAIN_STEP = TRAIN_STEP
         self.hist_step = hist_step   
         self.time_delay = time_delay
        
     def malfunc_(self,mal_id,mal_val=0.):
         if mal_id is not None:
            self.x[:,mal_id] = 0.
         else: pass     
        
     def sub_sample_(self):
         x_sub = np.split(self.x[:self.samp_rate*int(self.x.shape[0]/self.samp_rate)],int(self.x.shape[0]/self.samp_rate))
         x_sub = [sum(gg) for gg in x_sub] 
         self.x_sub = np.asarray(x_sub)
         self.y_sub = self.y[:self.samp_rate*int(self.x.shape[0]/self.samp_rate)][::self.samp_rate]
        
     def normalize_(self):
         self.x_mean, self.x_std = self.x_sub.mean(), self.x_sub.std()
         self.y_mean, self.y_std = self.y_sub.mean(), self.y_sub.std()  
        
         self.x_sub_norm = (self.x_sub - self.x_mean) / self.x_sub.std() 
         self.y_sub_norm = self.y_sub
         #self.y_sub_norm = (self.y_sub - self.y_mean) / self.y_sub.std() 
         #return self.x_sub_norm, self.y_sub_norm
         #return (self.x_sub - self.x_mean) / self.x_sub.std(), (self.y_sub - self.y_mean) / self.y_sub.std()   


     def inv_normalize_y_(self,y): 
         return y*self.y_std + self.y_mean
    
     def inv_normalize_x_(self,x): 
         return x*self.x_std + self.x_mean

     def get_feat_(self, x):
         x_feat = (x - self.x_mean) / self.x_sub.std()
         return torch.from_numpy(x_feat).float()

     def get_feats_(self):
         self.sub_sample_()
         self.normalize_()
            
         if self.feat_type == "hist":   
             x_hist = []   
             for i in range(self.hist_step):
                xx = np.mean(self.x_sub_norm[i:i-self.hist_step],axis=1)
                x_hist.append(xx)
             self.x_feats = np.stack(x_hist,axis=-1)
             self.y_feats = self.y_sub_norm[self.hist_step:]
        
         elif self.feat_type == "indiv": 
             self.x_feats = self.x_sub_norm[:-self.time_delay]
             self.y_feats = self.y_sub_norm[self.time_delay:]
        
         elif self.feat_type == "hist_indiv":   
             x_hist = []   
             for i in range(self.hist_step):
                xx = np.mean(self.x_sub_norm[i:i-self.hist_step],axis=1)
                x_hist.append(xx)
             x_hist = np.stack(x_hist,axis=-1) 
             self.x_feats = np.concatenate([self.x_sub_norm[:-self.hist_step],x_hist],axis=1)
             self.y_feats = self.y_sub_norm[self.hist_step:]
            
         elif self.feat_type == "long_hist_indiv":   
             x_hist = []   
             for i in range(self.hist_step):
                xx = np.mean(self.x_sub_norm[i:i-self.hist_step],axis=1)
                x_hist.append(xx)
             x_hist = np.stack(x_hist,axis=-1) 
             self.x_feats = np.concatenate([self.x_sub_norm[:-self.hist_step],x_hist],axis=1)
             self.x_feats = self.x_feats[:,[0,1,2,3,4,5,6,7,8,2*12,2*24,-1]]
             self.y_feats = self.y_sub_norm[self.hist_step:]
        
     def get_batches_(self,idx_start=10,idx_end=550,step=100):
         ### random samplimg batches from training data 
         idx = np.random.randint(idx_start,idx_end) 
         x_batch = self.x_feats[idx:idx+step]
         y_batch = self.y_feats[idx:idx+step]
         return torch.from_numpy(x_batch).float(),  torch.from_numpy(y_batch).float()
        
