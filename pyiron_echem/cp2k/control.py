from pyiron_base.generic.datacontainer import DataContainer

from pyiron_echem.cp2k.parser.utils import dict2inp
import copy

class Cp2kControl(DataContainer):
    
    def __init__(self, init=None, table_name=None, lazy=False, wrap_blacklist=(dict,)):
        #followed with datacontainer, what lazy and wrapblack_list mean?
        super().__init__(
                        init=init,
                        table_name=table_name,
                        lazy=lazy,
                        wrap_blacklist=wrap_blacklist,
                        )
        
        pass
    
    def _init_control(self):
        #由于__init__存在递归生成datacontainer  要重新清理input 模板的内容 init必须在整体control生成之后
        if not self["FORCE_EVAL"]["SUBSYS"].get("TOPOLOGY"):
            self["FORCE_EVAL"]["SUBSYS"] = {}
        
        self._remove_cell()
        self._remove_coord()
        self._remove_kind()
        self._remove_topo_coord()
        self._fill_topo()
        self.set_default_struct()
        self.set_default_global()
        #self.set_default_cell() 
        
        if self["FORCE_EVAL"].get("DFT"):
            self._remove_basisset_dir()
            self._remove_potential_dir()
        

    # @classmethod
    # def from_input_file(self, input_filename, canonical=False, loadfunc=aiida2dict):
        
    #     #using cp2k-input-tools to read a template input to save complex input settings
    #     #problem will be unclean template 
    #     input_dict = loadfunc(input_filename, canonical)
    #     return Cp2kControl(input_dict)
    
    
    
    @classmethod
    def from_input_dict(self, input_dict, *args, **qargs):
        
        #这里暂时没有做其他的格式识别, 另外需要在这里做一些dict清理
        #不能在
        input_dict = copy.deepcopy(input_dict)
        return Cp2kControl(input_dict, *args, **qargs)
    
    
    def as_input_dict_part(self,): #保留主input的树结构
        return self.to_builtin()
    
    def render(self, mode='local'):
        
        txt = dict2inp(self.as_nested_dict(), mode=mode)# TODO  可能会有问题，parser的选择等

        return txt
    
    def preview(self,):
        
        txt = self.render()
        print(txt)

    def _remove_kind(self):
        try:
            del self["FORCE_EVAL"]["SUBSYS"]["KIND"]
        except:
            pass
        
    def _remove_basisset_dir(self):
        del self["FORCE_EVAL"]["DFT"]["BASIS_SET_FILE_NAME"]
    
    def _remove_potential_dir(self):
        del self["FORCE_EVAL"]["DFT"]["POTENTIAL_FILE_NAME"]

    def _remove_cell(self):
        try:
            del self["FORCE_EVAL"]["SUBSYS"]["CELL"]
        except:
            pass #这里异常处理很简陋

    def _remove_coord(self):
        try:
            del self["FORCE_EVAL"]["SUBSYS"]["COORD"]
        except:
            pass #这里异常处理很简陋


    # def _clean_topology(self):
    #     try:
    #         del self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
    #     except:
    #         pass
    #     self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"] = {}

    def _fill_topo(self):
        SUBSYS = self["FORCE_EVAL"]["SUBSYS"]
        if not SUBSYS.get("TOPOLOGY"):
            SUBSYS["TOPOLOGY"] = {}


    def _remove_topo_coord(self):
        #TODO 如何适配不同的input文件 仍然是问题
        if self["FORCE_EVAL"]["SUBSYS"].get("TOPOLOGY"):
            TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        else:
            #TODO 以后报warning?
            return 
        if TOPO.get("COORD_FILE_FORMAT"):
            del TOPO["COORD_FILE_FORMAT"]
        if TOPO.get("COORD_FILE_FORMAT"):
            del TOPO["COORD_FILE_NAME"]

    def _remove_topo_conn(self):
        
        if self["FORCE_EVAL"]["SUBSYS"].get("TOPOLOGY"):
            TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        else:
            #TODO 以后报warning?
            return 
        if TOPO.get("CONN_FILE_NAME"):
            del TOPO["CONN_FILE_NAME"]
        if TOPO.get("CONNECTIVITY"):
            del TOPO["CONNECTIVITY"]

    def set_topo_conn(self, conn_file_name, conn_type="PSF"):
        TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        TOPO["CONNECTIVITY"] = conn_file_name
        TOPO["CONN_FILE_NAME"] = conn_type
        if not TOPO.get("DUMP_PSF"):
            TOPO["DUMP_PSF"] = {}

    def set_default_struct(self):
        
        TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        TOPO["COORD_FILE_FORMAT"] = "XYZ"
        TOPO["COORD_FILE_NAME"] = "./struct.xyz"
    
    def set_default_global(self):
        
        # if self.get("GLOBAL"):
        #     del self["GLOBAL"]
        # self.update({"GLOBAL":{}}, blacklist=(dict,))
        if self["GLOBAL"].get("PROJECT_NAME"):  #删除模板中多余的Project名称转换成Pyiron形式
            del  self["GLOBAL"]["PROJECT_NAME"]
        if self["GLOBAL"].get("PROJECT"):
            del  self["GLOBAL"]["PROJECT"]
        
        self["GLOBAL"]["PROJECT_NAME"]="pyiron"
        # self["GLOBAL"]["RUN_TYPE"] = "pyiron" #TODO 这里作为CP2K 关键词 不是任意的GEO_OPT MD 等
    
    def set_default_cell(self):
        
        self["FORCE_EVAL"]["SUBSYS"]["CELL"] = {}
        self["FORCE_EVAL"]["SUBSYS"]["CELL"]["CELL_FILE_FORMAT"] = "CP2K"
        self["FORCE_EVAL"]["SUBSYS"]["CELL"]["CELL_FILE_NAME"] = "cell.inp"
    
    
    def _remove_topo_molset(self):
        
        TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        assert TOPO["CONNECTIVITY "] == "MOL_SET"
        del TOPO["CONN_FILE_FORMAT"]
        del TOPO["MOL_SET"]
        del TOPO["CONNECTIVITY"]
    
    def _init_topo_molset(self):
        
        #self.clean_molset() TODO 还需要先clean吗
        TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        TOPO["CONNECTIVITY"] = "MOL_SET"
        TOPO["MOL_SET"] = {}
        TOPO["MOL_SET"]["MOLECULE"] = []
    
    def update_topo_molset(self, conn_filename, new_conn_nmol=None, new_conn_format=None, new_file_name=None):

        #由conn_filename关键词进行修改

        MOLECULE = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]["MOL_SET"]["MOLECULE"]
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
        
        MOLECULE = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]["MOL_SET"]["MOLECULE"]
        new_molecule = {
            "CONN_FILE_FORMAT":conn_format.upper(),
            "CONN_FILE_NAME": conn_filename,
            "NMOL":str(conn_num).upper()
        }
        MOLECULE.append(new_molecule)


    def enable_scf_ot(self):

        self["FORCE_EVAL"]["DFT"]["SCF"] = {
            'EPS_SCF': '1e-06',
            'MAX_SCF': '50',
            'SCF_GUESS': 'ATOMIC',
            'OUTER_SCF': {'EPS_SCF': '1e-06', 'MAX_SCF': '10'},
            'OT': {'ENERGY_GAP': '0.1',
            'PRECONDITIONER': 'FULL_SINGLE_INVERSE',
            'MINIMIZER': 'DIIS'}
            }


    def enable_scf_diagonal(self):

        self["FORCE_EVAL"]["DFT"]["SCF"] = {
            'SCF_GUESS': 'ATOMIC',
            'EPS_SCF': '3.0E-7',
            'MAX_SCF': '500',
            'ADDED_MOS': '500',
            'CHOLESKY': 'INVERSE',
            'SMEAR': {'_': 'ON',
            'METHOD': 'FERMI_DIRAC',
            'ELECTRONIC_TEMPERATURE': '[K] 300'},
            'DIAGONALIZATION': {'ALGORITHM': 'STANDARD'},
            'MIXING': {'METHOD': 'BROYDEN_MIXING',
            'ALPHA': '0.3',
            'BETA': '1.5',
            'NBROYDEN': '8'},
            'PRINT': {'RESTART': {'EACH': {'QS_SCF': '50'}, 'ADD_LAST': 'NUMERIC'}}
        }



    def _clean_scf_ot(self):
        SCF = self["FORCE_EVAL"]["DFT"]["SCF"]
        if SCF.get("OUTER_SCF"):
            del SCF["OUTER_SCF"]
        if SCF.get("OT"):
            del SCF["OT"]

        pass

    def _clean_scf_diagonal(self):
        # seems complecated
        SCF = self["FORCE_EVAL"]["DFT"]["SCF"]
        if SCF.get("DIAGONALIZATION"):
            del SCF["DIAGONALIZATION"]
        if SCF.get("ADDED_MOS"):
            del SCF["ADDED_MOS"]
        if SCF.get("CHOLESKY"):
            del SCF["CHOLESKY"]
        if SCF.get("SMEAR"):
            del SCF["SMEAR"]
        if SCF.get("SMEAR"):
            del SCF["SMEAR"]
        if SCF.get("MIXING"):
            del SCF["MIXING"]
        if SCF.get("PRINT"):
            del SCF["PRINT"]

        pass
