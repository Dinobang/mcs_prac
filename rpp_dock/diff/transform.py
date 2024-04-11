# добавление шума к положению белка-рецептора (поворот + перенос)
import numpy as np
import torch
import torch.nn as 
from torch_geometric.transforms import BaseTransform
from rpp_dock.utils.geom_utils import axis_angle_to_matrix, generate_angle

class NoiseTransform(BaseTransform):
    
    def __init__(self, args):

        self.noise_maker = Noise(args)
        self.noise_sceduler = NoiseSchedule()

    def __call__(self, protein):
        upd_protein = self.apply_noise(protein)
        return upd_protein
    
    def apply_noise(self, protein, t_update=True, rot_update=True):
        t_param, rot_param, time = self.noise_maker()

        self.noise_sceduler.set_time(protein.num_nodes)
        
        if t_update: 
            tr_vec = torch.normal(mean=0, std=t_param, size=(1, 3))
        if rot_update: 
            axis_angle = generate_angle(eps=rot_param)
            axis_angle = torch.from_numpy(axis_angle)
        
        return self.apply_updates(protein, tr_vec, axis_angle)


    def apply_updates(self, protein, tr_vec, axis_angle):
        center = torch.mean(protein.pos, dim=0, keepdim=True)
        rot_mat = axis_angle_to_matrix(axis_angle.squeeze())
        rigid_new_pos = (
            (protein.pos - center) @ rot_mat.T + tr_vec + center
        )
        protein.pos = rigid_new_pos
        return protein

        
class Noise:

    def __init__(self, args):
        self.t_min, self.t_max = args['t_min'], args['t_max'] 
        self.rot_min, self.rot_max = args['rot_min'], args['rot_max'] 

    def __call__(self):
        time = np.random.uniform()
        rot_param = self.rot_min*(1-time) + self.rot_max*time
        t_param = self.t_min*(1-time) + self.t_max*time
        return t_param, rot_param, time
    

class NoiseSchedule:
    def __init__(self):
        self.time_transf = []
        self.time_rotation = []

    def set_time(self, num_nodes, time,
            batch_size: int, device=None):
        lig_size = num_nodes
        self.time_transf.append(time * torch.ones(lig_size).to(device))
        self.time_rotation.append(time * torch.ones(lig_size).to(device))

    

    