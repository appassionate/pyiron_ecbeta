####mainly copied from https://github.com/pyiron/pyiron_contrib/pull/286/files, Author of pyiron, thanks for his work.

import os
import json
from pathlib import Path
import warnings

from pyiron import Project
from pyiron_base import DataContainer, state
from pyiron_base import GenericMaster


from pyiron_atomistics.atomistics.structure.atoms import pyiron_to_ase, ase_to_pyiron
from pyiron_atomistics.atomistics.job.atomistic import AtomisticGenericJob
from pyiron_atomistics.atomistics.structure.atoms import Atoms


from pyiron_echem.cp2k.structure import as_dict_from_struct, print_cell
from pyiron_echem.cp2k.control import Cp2kControl
from pyiron_echem.cp2k.content import Cp2kContent
from pyiron_echem.cp2k.visualize import Cp2kView

from pyiron_echem.cp2k.utils import merge_dict, merge_dict_within_copy

from pyiron_echem.cp2k.parser.utils import inp2dict, dict2inp

import ase.io as io



class Cp2kJob(AtomisticGenericJob):
    
    def __init__(self, project, job_name):

        super(Cp2kJob, self).__init__(project, job_name)
        self.__name__ = "cp2k"
        self.input = Cp2kInput()
        self.view = Cp2kView(self)
        
        self._executable_activate(enforce=True) 
     
    # adding pickle implements to special job, it might a wrong place
    def __reduce__(self, ):

        if self.status.initialized ==True:
            self._logger.info("pickling: job status is initialized, it will be saved by job.save() .")
            self.save()
        
        return (self._unpickle_J, (self.project.path, self.job_name))


    @classmethod
    def _unpickle_J(cls, project_path, job_name):
        
        pr = Project(project_path) #we cant just copy project for the job_type unpickable
        return pr[job_name]
    

    def to_hdf(self, hdf=None, group_name=None):
        """
        Store the ExampleJob object in the HDF5 File
        Args:
            hdf (ProjectHDFio): HDF5 group object - optional
            group_name (str): HDF5 subgroup name - optional
        """
        super(Cp2kJob, self).to_hdf(hdf=hdf, group_name=group_name)
        self._structure_to_hdf()
        self.input.to_hdf(self._hdf5)

    def from_hdf(self, hdf=None, group_name=None):
        """
        Restore the ExampleJob object in the HDF5 File
        Args:
            hdf (ProjectHDFio): HDF5 group object - optional
            group_name (str): HDF5 subgroup name - optional
        """
        super(Cp2kJob, self).from_hdf(hdf=hdf, group_name=group_name)
        self._structure_from_hdf()
        self.input.from_hdf(self._hdf5)

    def write_input(self):
        
        self._revise_walltime_by_run_time()
        self._write_cp2k_input()
        self._write_structure()
    
    def _revise_walltime_by_run_time(self):
        # revise walltime for elegant quit in cp2k program
        
        #when no server pointed WALLTIME will not be added.
        if self.server.run_time:
            self.input.content.GLOBAL["WALLTIME"] = \
                self.server.run_time-200
            assert int(self.input.content.GLOBAL["WALLTIME"]) > 0
        
    
    def _write_cp2k_input(self):
        
        _input = self.input.render_dict()
        cell_info = as_dict_from_struct(self.structure)
        merge_dict(_input, cell_info)
        final_input = dict2inp(_input, mode=self.input.parser)
        
        with open(os.path.join(self.working_directory,"input.inp"),"w") as f:
            f.write(final_input) #IO处理方式很简陋 也许pyiron有一些解决方案
            
        
    
    def _write_structure(self):
        atoms = pyiron_to_ase(self.structure)
        io.write(os.path.join(self.working_directory,"struct.xyz"), atoms)
        pass
    
    def _write_cp2k_cell(self):
        
        cell_info = as_dict_from_struct(self.structure, as_input_part=False)
        cell_input = print_cell(cell_info)
        
        with open(os.path.join(self.working_directory,"cell.inp"),"w") as f:
            f.write(cell_input) #IO处理方式很简陋 也许pyiron有一些解决方案

    # here restart will create a new job, within new infos
    def _restart_cp2k_job(self, job_name=None, job_type=None):
        

        # 1. 确定restart_file_list哪些是要复制的
        ## .restart文件（包含位置信息？）
        ## pyiron-RESTART.wfn* 文件
        ## 

        import copy
        if job_type==None:
            job_type = Cp2kJob


        new_ham = super(AtomisticGenericJob, self).restart(
            job_name=job_name, job_type=job_type
        )

        # new_ham.structure = self.structure.copy()
        # new_ham.input = copy.deepcopy(self.input) 

        if isinstance(new_ham, GenericMaster) and not isinstance(self, GenericMaster):
            new_child = self.restart(job_name=None, job_type=None)
            new_ham.append(new_child)

        #cp2k重启的机制就是复制原来给的Input文件
        new_ham.structure = self.structure.copy()
        new_ham.input = copy.deepcopy(self.input)

        new_ham._generic_input["structure"] = "atoms"

        #add restart_file for launch restart job 
        if new_ham.__name__ == self.__name__:
            new_ham.restart_file_list.append(self.get_workdir_file("pyiron-1.restart"))
        
        # using pyiron-1.restart in restart_job.input
        new_ham.input.content["EXT_RESTART"] = {}
        new_ham.input.content["EXT_RESTART"]["RESTART_FILE_NAME"] = "./pyiron-1.restart"
        #重新设置 任务的counters
        #new_ham.input.content["EXT_RESTART"]["RESTART_COUNTERS"] = True


        return new_ham


    def _restart_cp2k_job_from_wfn(self, job_name=None, job_type=None):
        
        
        new_ham = self._restart_cp2k_job(job_name, job_type)
        
        #add wfn* to restart_file_list
        if new_ham.__name__ == self.__name__:
            wfn_list = list(Path(self.working_directory).glob("pyiron-RESTART.wfn"))
            # TODO: 同一个project尽量用相对路径吧
            for wfn_file in wfn_list:
                new_ham.restart_file_list.append(str(wfn_file))
        
        # using wfn file in restart 
        new_ham.input.content["FORCE_EVAL"]["DFT"]["WFN_RESTART_FILE_NAME"] = './pyiron-RESTART.wfn'
        new_ham.input.content["FORCE_EVAL"]["DFT"]["SCF"]["SCF_GUESS"] = "RESTART"
            
        return new_ham


    #restart 的实现
    def read_restart_file(self):

        # 参考lammpsbase
        #                
        pass


    def restart(self, job_name=None, job_type=None):
        
        """
        Restart a new job created from an existing Lammps calculation.
        Args:
            project (pyiron_atomistics.project.Project instance): Project instance at which the new job should be created
            job_name (str): Job name
            job_type (str): Job type. If not specified a Lammps job type is assumed

        Returns:
            new_ham (lammps.lammps.Lammps instance): New job
        """
        new_ham = super(Cp2kJob, self).restart(job_name=job_name, job_type=self.__class__)
        # if new_ham.__name__ == self.__name__:
        #     new_ham.potential = self.potential
        #     new_ham.read_restart_file(filename="restart.out")
        #     new_ham.read_restart_file.append(self.get_workdir_file("restart.out"))
        return new_ham


    def collect_xyz_file(self, file_pattern="pyiron-pos-1.xyz", cwd=None):

        files = list(Path(self.job_file_name(file_name="", cwd=cwd)).glob(file_pattern))
        if not files:
            warnings.warn(f"CP2K warning: No {file_pattern} output file found.")
            return 

        file_name = files[0].name
        # TODO: here we just saved the name but not the positions
        with self.project_hdf5.open("output/generic") as hdf_output:
            hdf_output["xyz_filename"] = file_name



    def collect_output(self):

        self.collect_xyz_file(file_pattern="pyiron-pos-1.xyz", cwd=self.working_directory)

        self.input.from_hdf(self._hdf5)


    def get_cp2k_frame(self, index=-1, pbc=True):
        #使用mda读取轨迹, 避免速度过慢
        from MDAnalysis import Universe
        from ase import Atoms
        
        posfile = self.job_file_name("pyiron-pos-1.xyz")
        uni = Universe(posfile)
        
        return Atoms(
            uni.atoms.elements, 
            positions=uni.trajectory[index].positions,
            cell = self.structure.cell,
            pbc=pbc
        )


class Cp2kInput():
    
    def __init__(self, parser="local"):
        
        #TODO:
        
        self.content = Cp2kContent(table_name="cp2k_content")
        self.parser=parser
        self.control = Cp2kControl(self)
        #psf文件应该怎么输出和导入，这是个问题
    
    def from_input_file(self, input_filename, *fargs, **fkwargs):


        
        input_dict = inp2dict(input_filename, mode=self.parser, *fargs, **fkwargs)
        self.from_input_dict(input_dict)

    def from_input_dict(self, input_dict):

        self.content = Cp2kContent.from_input_dict(input_dict, table_name="cp2k_content")
        self.content._init_content()
        #self.control #TODO 

    def update_input_dict(self, updated_dict):
        
        _dict = self.render_dict().copy()
        # how to check updated_dict?
        _dict = merge_dict_within_copy(_dict, updated_dict)
        self.from_input_dict(_dict)
    
    def render_dict(self):
        
        total = {}
        merge_dict(total, self.content.as_input_dict_part())

        return total
    
    def render_input_dict(self):

        inp = self.render_dict()

        return dict2inp(inp, mode=self.parser)
    
    def preview(self,):
        
        txt = self.render_input_dict()
        print(txt)
        
    def to_hdf(self, hdf):
        """
         
        """
        with hdf.open("input") as hdf5_input:
            self.content.to_hdf(hdf5_input,"content")
            #self.kind.to_hdf(hdf5_input,"kind")

    def from_hdf(self, hdf):
        """
        hdf5 node to deserialize datacontainer 
        """
        with hdf.open("input") as hdf5_input:
            self.content.from_hdf(hdf5_input,"content")

