#关于structure的部分 要写一些方法 构造CELL, 信息
from pyiron import ase_to_pyiron

from ase import Atoms
import numpy as np


def as_dict_from_struct(struct, as_input_part=True):
    
    #没有考虑分数坐标
    if type(struct) == Atoms:
        struct = ase_to_pyiron(struct)
    # 根据structure 生成CELL PBC
    
    cell_dict = {
                "A": "    ".join([str(_) for _ in struct.cell.array[0].tolist()]),
                "B": "    ".join([str(_) for _ in struct.cell.array[1].tolist()]),
                "C": "    ".join([str(_) for _ in struct.cell.array[2].tolist()]),
                "PERIODIC":"".join(np.array(["X","Y","Z"])[struct.pbc].tolist())
            }
    if (struct.pbc == False).all():
        cell_dict["PERIODIC"] = "NONE" #解決不设置pbc时候的bug
    
    if as_input_part:
        return {"FORCE_EVAL":{"SUBSYS":{"CELL":cell_dict}}}
    else:
        return cell_dict

def print_cell(cell_dict):
    
    line_A = f"A {cell_dict['A']}\n"
    line_B = f"B {cell_dict['B']}\n"
    line_C = f"C {cell_dict['C']}\n"
    period = f"PERIODIC {cell_dict['PERIODIC']}\n"
    
    return line_A+line_B+line_C+period


def celldict2cell():
    
    pass



def struct_from_input():
    
    #把Input的结构(包括cell信息)转化成Atoms对象
    pass