from pathlib import Path
import copy

def merge_dict(total_dct, item_dic):
    """
    copied from https://github.com/aiidateam/aiida-cp2k/blob/develop/aiida_cp2k/utils/workchains.py
    merging dict is used frequently when processing nested software inputs.
    """
    from collections.abc import Mapping

    for k, _ in item_dic.items():  # it was .iteritems() in python2
        if k in total_dct and isinstance(total_dct[k], dict) and isinstance(item_dic[k], Mapping):
            merge_dict(total_dct[k], item_dic[k])
        else:
            total_dct[k] = item_dic[k]

