from pyiron_base.storage.datacontainer import DataContainer

from pyiron_echem.cp2k.parser.utils import dict2inp
import copy

# now, Cp2kContent inherent the old-fashioned  Cp2kControl
# Cp2kContent is DataContainer in pyiron_base to parse the cp2k input dict
class Cp2kContent(DataContainer):
    
    def __init__(self, init=None, table_name=None, lazy=False, wrap_blacklist=()):
        # wrap_blacklist will ignore the chosen dataclass type not trans to datacontainer
        # in Cp2kContent, we should be careful the existing list type   
        #followed with datacontainer, what lazy and wrapblack_list mean?
        super().__init__(
                        init=init,
                        table_name=table_name,
                        lazy=lazy,
                        wrap_blacklist=wrap_blacklist,
                        )
        pass
    
    # def __repr__(self): #currently, cant work
    #     return self.as_view_part()
    
    def _check_content_root(self):
        # some content change method should not be applied in a sub-DataContainter class
        # u should apple those mehod before check the container
        try:
            assert self.table_name == "cp2k_content"
        except:
            raise ValueError("current Cp2kContext are not in root structure!")
                
    def _init_content(self):
        
        # to remove loaded coord and cell, which will generated from in Cp2kJob.structure info.
        self._remove_cell()
        self._remove_coord()
        self._remove_topo_coord()
        
        self._fill_topo()
        self.set_default_struct()
        self.set_default_global()
        
        # if self["FORCE_EVAL"].get("DFT"):
        #     self._remove_basisset_dir()
        #     self._remove_potential_dir()
        

    # @classmethod
    # def from_input_file(self, input_filename, canonical=False, loadfunc=aiida2dict):
        
    #     #using cp2k-input-tools to read a template input to save complex input settings
    #     #problem will be unclean template 
    #     input_dict = loadfunc(input_filename, canonical)
    #     return Cp2kControl(input_dict)
    
    
    @classmethod
    def from_input_dict(self, input_dict, *args, **qargs):
        
        input_dict = copy.deepcopy(input_dict)
        return Cp2kContent(input_dict, *args, **qargs)
    
    def as_input_dict_part(self,): 
        self._check_content_root()
        
        return self.to_builtin()
    
    def render(self, mode='local'):
        self._check_content_root()
        txt = dict2inp(self.to_builtin(), mode=mode)

        return txt
    
    def preview(self,):
        
        txt = self.render()
        print(txt)
    
    def as_view_part(self):
        txt = dict2inp(self.to_builtin(),)
        return txt
    def preview_part(self):
        print(self.as_view_part())
    
    def _remove_kind(self):
        self._check_content_root()
        try:
            del self["FORCE_EVAL"]["SUBSYS"]["KIND"]
        except:
            pass

    def _remove_cell(self):
        self._check_content_root()
        try:
            del self["FORCE_EVAL"]["SUBSYS"]["CELL"]
        except:
            pass

    def _remove_coord(self):
        self._check_content_root()
        try:
            del self["FORCE_EVAL"]["SUBSYS"]["COORD"]
        except:
            pass 

    def _remove_topo_coord(self):
        self._check_content_root()
        if self["FORCE_EVAL"]["SUBSYS"].get("TOPOLOGY"):
            TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        else:
            return 
        if TOPO.get("COORD_FILE_FORMAT"):
            del TOPO["COORD_FILE_FORMAT"]
        if TOPO.get("COORD_FILE_FORMAT"):
            del TOPO["COORD_FILE_NAME"]

    def _fill_topo(self):
        self._check_content_root()
        SUBSYS = self["FORCE_EVAL"]["SUBSYS"]
        if not SUBSYS.get("TOPOLOGY"):
            SUBSYS["TOPOLOGY"] = {}

    def set_default_struct(self):
        
        TOPO = self["FORCE_EVAL"]["SUBSYS"]["TOPOLOGY"]
        TOPO["COORD_FILE_FORMAT"] = "XYZ"
        TOPO["COORD_FILE_NAME"] = "./struct.xyz"
    
    def set_default_global(self):
        
        # if self.get("GLOBAL"):
        #     del self["GLOBAL"]
        # self.update({"GLOBAL":{}}, blacklist=(dict,))
        if self["GLOBAL"].get("PROJECT_NAME"): 
            del  self["GLOBAL"]["PROJECT_NAME"]
        if self["GLOBAL"].get("PROJECT"):
            del  self["GLOBAL"]["PROJECT"]
        
        #set every CP2K output data name as pyiron-* type 
        self["GLOBAL"]["PROJECT_NAME"]="pyiron"
