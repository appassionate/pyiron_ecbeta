import pathlib

#copied from ecint
_E_WITH_Q = {'H': '1', 'He': '2', 'Li': '3', 'Be': '4', 'B': '3', 'C': '4',
             'N': '5', 'O': '6', 'F': '7', 'Ne': '8',
             'Na': '9', 'Mg': '2', 'Al': '3', 'Si': '4', 'P': '5', 'S': '6',
             'Cl': '7', 'Ar': '8', 'K': '9', 'Ca': '10',
             'Sc': '11', 'Ti': '12', 'V': '13', 'Cr': '14', 'Mn': '15',
             'Fe': '16', 'Co': '17', 'Ni': '18', 'Cu': '11',
             'Zn': '12', 'Ga': '3', 'Ge': '4', 'As': '5', 'Se': '6', 'Br': '7',
             'Kr': '8',
             'Rb': '9', 'Sr': '10', 'Y': '11', 'Zr': '12', 'Nb': '13',
             'Mo': '14', 'Tc': '15', 'Ru': '8', 'Rh': '9',
             'Pd': '18', 'Ag': '11', 'Cd': '12', 'In': '3', 'Sn': '4',
             'Sb': '5', 'Te': '6', 'I': '7', 'Xe': '8',
             'Cs': '9', 'Ba': '10', 'La': '11', 'Hf': '12', 'Ta': '5', 'W': '6',
             'Re': '7', 'Os': '8', 'Ir': '9',
             'Pt': '18', 'Au': '19', 'Hg': '12', 'Tl': '3', 'Pb': '4',
             'Bi': '5', 'Po': '6', 'At': '7', 'Rn': '8'}




#followed with cp2k-input-tools
DEFAULT_CP2K_INPUT_XML = pathlib.Path(__file__).resolve().parent.joinpath("./xmls/cp2k_input_dpmd.xml")
