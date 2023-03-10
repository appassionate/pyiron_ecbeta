from pathlib import Path
import copy

def merge_dict(total_dct, item_dict):
    """
    copied from https://github.com/aiidateam/aiida-cp2k/blob/develop/aiida_cp2k/utils/workchains.py
    
    """
    from collections.abc import Mapping
    for k, _ in item_dict.items():  # it was .iteritems() in python2
        if k in total_dct and isinstance(total_dct[k], dict) and isinstance(item_dict[k], Mapping):
            merge_dict(total_dct[k], item_dict[k])
        else:
            total_dct[k] = item_dict[k]

def merge_dict_within_copy(total_dct, item_dict):
    """
    modified from merge_dict
    
    """
    from collections.abc import Mapping
    from copy import deepcopy
    total_dct = deepcopy(total_dct) 
    #recursive merge
    for k, _ in item_dict.items(): 
        if k in total_dct and isinstance(total_dct[k], dict) and isinstance(item_dict[k], Mapping):
            merge_dict(total_dct[k], item_dict[k])
        else:
            total_dct[k] = item_dict[k]
    return total_dct


def trans_old_h5_to_new(hdf5_file_path):
    import os
    from pathlib import Path
    import h5py
    hdf5_file_path = os.path.abspath(hdf5_file_path)
    job_name = Path(hdf5_file_path).name[:-3]
    # remain previous control node, copy the new content node
    with h5py.File(hdf5_file_path, 'r+') as f:
        _input = f[f"{job_name}/input/"]
        _input.copy('control','content')