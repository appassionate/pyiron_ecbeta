import copy

from pyiron_echem.cp2k import _E_WITH_Q
from pyiron_base.generic.datacontainer import DataContainer


class Cp2kKind(DataContainer):

    def __init__(self,
                init=None,
                table_name=None,
                lazy=False,
                wrap_blacklist=(dict,),
                **qwargs):

        pass

    pass



class Cp2kDFTKind(DataContainer):
    
    #vasp 中可以拆分成potential和basis_set但是cp2k 是kind对象耦合在一起的
    
    def __init__(self,
                init=None,
                table_name=None,
                lazy=False,
                wrap_blacklist=(dict,),
                elements=None,
                special_kind=None,
                basis_set_filename="BASIS_MOLOPT",
                potential_filename="GTH_POTENTIALS",
                basis_set_prefix="DZVP-MOLOPT-SR-GTH",
                potential_prefix="GTH-PBE",
                basis_suffix="",
                potential_suffix="",
                **qwargs):
        #followed with datacontainer, what lazy and wrapblack_list mean?
        super().__init__(
                        init=init,
                        table_name=table_name,
                        lazy=lazy,
                        wrap_blacklist=wrap_blacklist,
                        )

        self.basis_set_filename = basis_set_filename
        self.potential_filename = potential_filename

        self.basis_set_prefix = basis_set_prefix
        self.potential_prefix = potential_prefix
        self.basis_suffix = basis_suffix
        self.potential_suffix = potential_suffix
        
        self.kind = {}
        if special_kind:
            self.kind.update(special_kind,) #这里丧失了递归的datacontainer结构
        if elements:
            for ele in elements:
                if not self.kind.get(ele,None):
                    self.kind[ele] = {"basis_set": self.basis_set_prefix+self.basis_suffix,
                                "potential": self.potential_prefix+"-q"+_E_WITH_Q[ele]+self.potential_suffix
                                }
    @classmethod
    def from_structure(self, structure, *args, **qwargs):
        
        from pyiron_atomistics.atomistics.structure.atoms import Atoms as pyiron_structure
        assert type(structure) == pyiron_structure
        eles = [ele["Abbreviation"] for ele in structure.elements]
        eles = list(set(eles))
        
        return Cp2kDFTKind(elements=eles, *args, **qwargs)
    
    @classmethod
    def from_input_dict(self, input_dict, *args, **qargs):
        #从完整的 input dict中得到对应信息
        special_kind = {}
        try:
            input_dict = copy.deepcopy(input_dict)
            kind_list = input_dict["FORCE_EVAL"]["SUBSYS"]["KIND"]
            for _kind in kind_list:
                special_kind.update({
                    _kind["_"]:{
                        "potential":_kind["POTENTIAL"],
                        "basis_set":_kind["BASIS_SET"],
                    }
                })
            
            basisset_filename = input_dict["FORCE_EVAL"]["DFT"]["BASIS_SET_FILE_NAME"]
            potential_filename = input_dict["FORCE_EVAL"]["DFT"]["POTENTIAL_FILE_NAME"]
            return Cp2kDFTKind(
                special_kind=special_kind,
                basis_set_filename=basisset_filename,
                potential_filename=potential_filename,
            )
        except:
            print("failed read kind section from input dict, init a empty kind")
            return Cp2kDFTKind()#失败则初始化一个空对象
    

    
    def as_input_dict_part(self):
        return {
            "FORCE_EVAL":{
                "DFT":{
                    "BASIS_SET_FILE_NAME": self.basis_set_filename,
                    "POTENTIAL_FILE_NAME": self.potential_filename,
                },
                "SUBSYS":{
                    "KIND":[{'_': ele,
                        'POTENTIAL': kind_info['potential'],
                        'BASIS_SET': kind_info['basis_set']} for ele, kind_info in self.kind.items()]
                    }
                }
        }


class Cp2kMMKind(DataContainer):

    def __init__(self,
                init=None,
                table_name=None,
                lazy=False,
                wrap_blacklist=(dict,),
                **qwargs):

        #followed with datacontainer, what lazy and wrapblack_list mean?
        super().__init__(
                        init=init,
                        table_name=table_name,
                        lazy=lazy,
                        wrap_blacklist=wrap_blacklist,
                        )

        self.kind = DataContainer()

        pass


    @classmethod
    def from_input_dict(self, input_dict, *args, **qargs):
        #从完整的 input dict中得到对应信息
        kind_dict = {}
        try:
            input_dict = copy.deepcopy(input_dict)
            kind_list = input_dict["FORCE_EVAL"]["SUBSYS"]["KIND"]
            for _kind in kind_list:
                prop_names = list(filter(lambda x : x != '_', _kind))
                kind_dict.update({
                    _kind["_"]:{
                        prop_name:_kind[prop_name] for prop_name in prop_names
                    }
                })
            kind = Cp2kMMKind()
            kind.kind.update(kind_dict)

            return kind
        except:
            print("failed read kind section from input dict, init a empty kind")
            return Cp2kDFTKind()#失败则初始化一个空对象
    
    #@classmethod
    def from_structure(self, ):
        
        #TODO
        #不依赖input 以结构中的原子种类 构造kind

        pass


    def as_input_dict_part(self):
        return {
            "FORCE_EVAL":{
                "MM":{
                },
                "SUBSYS":{
                    "KIND":[{'_': ele,**kind_info} for ele, kind_info in self.kind.items()]
                    }
                }
        }