import os
import pandas as pd
from pathlib import Path

from pyiron_atomistics.lammps.potential import LammpsPotential


def get_dp_potential(potential_files, type_map, out_freq=1000, potential_name="MLP_DP", rel_start_path=None):

    potential_files = [str(Path(_file_path).absolute()) for _file_path in potential_files]
    
    if rel_start_path:
        rel_potential_files =  [os.path.relpath(_p, rel_start_path) for _p in potential_files]
    else:
        rel_potential_files = potential_files
    
    print(potential_files)
    #TODO: 考虑远程和本地如何引入势函数的路径的问题
    
    
    dpmd_pot = pd.DataFrame(
        {
        'Name': [potential_name],
        'Filename': [[]],
        'Model': ['Custom'],
        'Species': [[]],
        'Config': [["pair_style     deepmd ",]+
                   [str(pot) +" &\n" for pot in rel_potential_files]+
                   [f"out_freq {out_freq} "]+
                   ["out_file model_devi.out \n"]+
                   ["pair_coeff * *"], #revise to fit dpmdkit 2.0
                  ]
        })
    
    dpmd_pot["Species"] = (type_map,)
    dpmd_pot["Filename"] = (potential_files,)
    
    return dpmd_pot

# here we inherient LammpsPotential

class ECLammpsPotential(LammpsPotential):
    
    def __init__(self, input_file_name=None):
        super(LammpsPotential, self).__init__(
            input_file_name=input_file_name,
            table_name="potential_inp",
            comment_char="#",
        )
        self._potential = None
        self._attributes = {}
        self._df = None
        self._symlink_by_default =True
        self._enable_copy = True
    
    # TODO:
    # 增加一个touch job_name using lock的逻辑, 当任务完成后删掉对应于job_name的lock
    # 暂时没有考虑potential删除的逻辑
    # cache potential的md5码 完成对应文件的验证 

    #need some method to verify the potential file    
    # def verify_potential_file_mdf5():
        
    #     pass
    

    
    def symlink_pot_files(self, working_directory):
        if self.files is not None:
            for _path_pot in self.files:
                dst_path = Path(working_directory).joinpath(Path(_path_pot).name)
                print(_path_pot)
                print(dst_path)
                if not os.path.exists(dst_path): #TODO:临时避免现在的重复连接的问题
                    os.symlink(_path_pot, dst_path)
    
    def load_dp_potential(self, pot_files, type_map, out_freq=1000, potential_name="MLP_DP", rel_start_path=None):
        
        self.df = get_dp_potential(pot_files, type_map, out_freq, potential_name, rel_start_path=rel_start_path)
    
    #currently, we might ruin the file-existing check in LammpsPotential for symlink 
