from pyiron_atomistics.atomistics.structure.atoms import ase_to_pyiron

from ase import Atoms
import numpy as np


def as_dict_from_struct(struct, as_input_part=True):
    
    if type(struct) == Atoms:
        struct = ase_to_pyiron(struct)
    
    cell_dict = {
                "A": "    ".join([str(_) for _ in struct.cell.array[0].tolist()]),
                "B": "    ".join([str(_) for _ in struct.cell.array[1].tolist()]),
                "C": "    ".join([str(_) for _ in struct.cell.array[2].tolist()]),
                "PERIODIC":"".join(np.array(["X","Y","Z"])[struct.pbc].tolist())
            }
    if (struct.pbc == False).all():
        cell_dict["PERIODIC"] = "NONE"
    
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



def struct_from_input():
    
    pass