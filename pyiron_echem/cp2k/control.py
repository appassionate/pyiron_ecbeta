from pyiron_base.state import state
from pyiron_echem.cp2k.content import Cp2kContent


class Cp2kControl():
    
    def __init__(self, cp2kinput):
        
        self._input = cp2kinput
        self._logger = state.logger
        
        #check it not be recursive init
        #TODO:seems bug
        #self._input.content = self._input.content
        

    def _remove_basisset_dir(self):
        
        del self._input.content["FORCE_EVAL"]["DFT"]["BASIS_SET_FILE_NAME"]
    
    def _remove_potential_dir(self):
        del self._input.content["FORCE_EVAL"]["DFT"]["POTENTIAL_FILE_NAME"]


    def _clean_topology(self):
        try:
            del self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        except:
            pass
        self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"] = {}


    def _remove_topo_conn(self):
        
        if self._input.content["FORCE_EVAL"]["SUBSYS"].get("TOPOLOGY"):
            TOPO = self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        else:
            #TODO 以后报warning?
            return 
        if TOPO.get("CONN_FILE_NAME"):
            del TOPO["CONN_FILE_NAME"]
        if TOPO.get("CONNECTIVITY"):
            del TOPO["CONNECTIVITY"]

    def set_topo_conn(self, conn_file_name, conn_type="PSF"):
        TOPO = self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        TOPO["CONNECTIVITY"] = conn_file_name
        TOPO["CONN_FILE_NAME"] = conn_type
        if not TOPO.get("DUMP_PSF"):
            TOPO["DUMP_PSF"] = {}

    
    def set_default_cell(self):
        # TODO: it cant be run successfully
        self._input.content["FORCE_EVAL"]["SUBSYS"]["CELL"] = {}
        self._input.content["FORCE_EVAL"]["SUBSYS"]["CELL"]["CELL_FILE_FORMAT"] = "CP2K"
        self._input.content["FORCE_EVAL"]["SUBSYS"]["CELL"]["CELL_FILE_NAME"] = "cell.inp"
    
    
    def _remove_topo_molset(self):
        
        TOPO = self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        assert TOPO["CONNECTIVITY "] == "MOL_SET"
        del TOPO["CONN_FILE_FORMAT"]
        del TOPO["MOL_SET"]
        del TOPO["CONNECTIVITY"]
    
    def _init_topo_molset(self):
        
        TOPO = self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        TOPO["CONNECTIVITY"] = "MOL_SET"
        TOPO["MOL_SET"] = {}
        TOPO["MOL_SET"]["MOLECULE"] = []
    

    def update_topo_molset(self, conn_filename, new_conn_nmol=None, new_conn_format=None, new_file_name=None):

        #根据conn_filename关键词寻找对应的idx, 进行修改
        #update 方法更新MOL_SET MOLECULE中的分子信息

        MOLECULE = self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]["MOL_SET"]["MOLECULE"]
        conn_idx = 'not'
        for idx, mol in enumerate(MOLECULE):
            if mol["CONN_FILE_NAME"] == conn_filename:
                conn_idx = idx
        if conn_idx=='not':
            print("conn_filename not found")
            return
        if not new_file_name:
            new_file_name = conn_filename
        if not new_conn_nmol:
            new_conn_nmol = MOLECULE[conn_idx]["NMOL"]
        if not new_conn_format:
            new_conn_format = MOLECULE[conn_idx]["CONN_FILE_FORMAT"]

        MOLECULE[conn_idx] = {
            "CONN_FILE_FORMAT":new_conn_format.upper(),
            "CONN_FILE_NAME": new_file_name,
            "NMOL":str(new_conn_nmol).upper()
        }

    def add_topo_molset(self, conn_filename, conn_num, conn_format="PSF"):
        
        MOLECULE = self._input.content["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]["MOL_SET"]["MOLECULE"]
        new_molecule = {
            "CONN_FILE_FORMAT":conn_format.upper(),
            "CONN_FILE_NAME": conn_filename,
            "NMOL":str(conn_num).upper()
        }
        MOLECULE.append(new_molecule)


    def _enable_dft_calculation():
        
        # 1. DFT kindsection 
        # 2. SCF
        # 3. KIND settings
        # 4. basisset and pseudo..
        
        pass

    def enable_dft(self, algorithm="OT"):
        
        self._input.content["FORCE_EVAL"]["DFT"] = Cp2kContent({})
        self.set_dft_basis_and_potential_file()
        self.set_dft_qs()
        self.set_dft_xc()
        
        if algorithm in ("OT", "ot"):
            self.enable_dft_scf_ot()
        elif algorithm in ("DIAG", "diag"):
            self.enable_dft_scf_diagonal()
        

    def set_dft_basis_and_potential_file(self, 
                                         basis_file="BASIS_MOLOPT",
                                         potential_file="GTH_POTENTIALS"):
        self._input.content["FORCE_EVAL"]["DFT"]["BASIS_SET_FILE_NAME"] = basis_file
        self._input.content["FORCE_EVAL"]["DFT"]["POTENTIAL_FILE_NAME"] = potential_file

    def set_dft_multip(self, multip=1):
        self._input.content["FORCE_EVAL"]["DFT"]["MULTIP"] = multip
    def set_dft_plus_u_method(self, multip=1):
        self._input.content["FORCE_EVAL"]["DFT"]["MULTIP"] = multip
    def set_dft_qs(self, eps_default=1.0E-13):
        _template = {"QS":{"EPS_DEFAULT":eps_default}}
        self._input.content["FORCE_EVAL"]["DFT"] = Cp2kContent(_template)
    def set_dft_xc(self, xc_functional='PBE'):
        _template = {"XC":{"XC_FUNCTIONAL":xc_functional}}
        self._input.content["FORCE_EVAL"]["DFT"] = Cp2kContent(_template)

    def set_dft_print_pdos_and_hatree(self, each_md_step=None, enable_pdos=True, enable_hatree=True):

        if each_md_step:
            try:
                assert self._input.contentt["GLOBAL"]["RUN_TYPE"] == "MD"
            except:
                raise ValueError("wrong RUN_TYPE, you cant dft md_step in no MD tasks.")
        _template = {'PDOS': {'ADD_LAST': 'NUMERIC',
            'APPEND': '.TRUE.',
            'COMMON_ITERATION_LEVELS': '0',
            'COMPONENTS': '',
            'EACH': {'GEO_OPT': '0'},
            'NLUMO': '-1'},
            'V_HARTREE_CUBE': {'ADD_LAST': 'NUMERIC',
            'APPEND': '.TRUE.',
            'COMMON_ITERATION_LEVELS': '0',
            'EACH': {'GEO_OPT': '0'}}}
        if each_md_step:
            _template["PDOS"]["EACH"]["MD"] = each_md_step
            _template["V_HARTREE_CUBE"]["EACH"]["MD"] = each_md_step
        if not enable_pdos:
            del _template["PDOS"]
        if not enable_hatree:
            del _template["V_HARTREE_CUBE"]
        
        self._input.content["FORCE_EVAL"]["DFT"]["PRINT"] = Cp2kContent(_template)
        pass

    def _clean_dft_scf(self):
        self._input.content["FORCE_EVAL"]["DFT"].pop("SCF", None)

    def enable_dft_scf_ot(self):
        
        self._clean_dft_scf()
        _template = {
            'EPS_SCF': '1e-06',
            'MAX_SCF': '50',
            'SCF_GUESS': 'ATOMIC',
            'OUTER_SCF': {'EPS_SCF': '1e-06', 
                          'MAX_SCF': '10'},
            'OT': {
                'ENERGY_GAP': '0.1',
                'PRECONDITIONER': 'FULL_SINGLE_INVERSE',
                'MINIMIZER': 'DIIS'
                }
            }
        self._input.content["FORCE_EVAL"]["DFT"]["SCF"] = Cp2kContent(_template)


    def enable_dft_scf_diagonal(self):
        
        self._clean_dft_scf()
        _template = {
            'SCF_GUESS': 'ATOMIC',
            'EPS_SCF': '3.0E-7',
            'MAX_SCF': '500', #1500
            'ADDED_MOS': '500',
            'CHOLESKY': 'INVERSE',
            'SMEAR': {'_': 'ON',
                      'METHOD': 'FERMI_DIRAC',
                      'ELECTRONIC_TEMPERATURE': '[K] 300'
                },
            'DIAGONALIZATION': {
                'ALGORITHM': 'STANDARD'
                },
            'MIXING': {'METHOD': 'BROYDEN_MIXING',
                       'ALPHA': '0.3',
                       'BETA': '1.5',
                       'NBROYDEN': '8'},
            'PRINT': {
                'RESTART': {
                    'EACH': {
                        'QS_SCF': '50'
                        }, 
                    'ADD_LAST': 'NUMERIC'}}
        }
        self._input.content["FORCE_EVAL"]["DFT"]["SCF"] = Cp2kContent(_template)


    # def _clean_scf_ot(self):
    #     SCF = self._input.content["FORCE_EVAL"]["DFT"]["SCF"]
    #     keys_to_delete = ["OUTER_SCF", "OT"]
    #     for key in keys_to_delete:
    #         SCF.pop(key, None)

    #     pass

    # def _clean_scf_diagonal(self):
    #     # seems complecated
    #     SCF = self._input.content["FORCE_EVAL"]["DFT"]["SCF"]
    #     keys_to_delete = ["DIAGONALIZATION", "ADDED_MOS", "CHOLESKY", "SMEAR", "MIXING", "PRINT"]
    #     for key in keys_to_delete:
    #         SCF.pop(key, None)

    #     pass
