####mainly copied from https://github.com/pyiron/pyiron_contrib/pull/286/files, Author of pyiron, thanks for his work.

import os
import json
from pathlib import Path
import warnings

from pyiron import Project
from pyiron_base import DataContainer, state
from pyiron_base.jobs.job.extension.executable import Executable
from pyiron_base import GenericMaster


from pyiron_atomistics.atomistics.structure.atoms import pyiron_to_ase, ase_to_pyiron
from pyiron_atomistics.atomistics.job.atomistic import AtomisticGenericJob
from pyiron_atomistics.atomistics.structure.atoms import Atoms


from pyiron_echem.cp2k.structure import as_dict_from_struct, print_cell
from pyiron_echem.cp2k.kind import Cp2kDFTKind, Cp2kMMKind
from pyiron_echem.cp2k.control import Cp2kControl
from pyiron_echem.cp2k.utils import merge_dict

from pyiron_echem.cp2k.parser.utils import inp2dict, dict2inp

import ase.io as io

#是否引入mda, 有待考虑
from MDAnalysis import Universe

kind_dict = {
    "DFT":Cp2kDFTKind,
    "MM":Cp2kMMKind,
    }

def choose_ff_type(input_dict, ):

    force_eval = input_dict["FORCE_EVAL"]
    if "DFT" in force_eval.keys():
        return "DFT"
    if "MM" in force_eval.keys():
        return "MM"


class Cp2kJob(AtomisticGenericJob):
    
    def __init__(self, project, job_name):

        super(Cp2kJob, self).__init__(project, job_name)
        self.__name__ = "cp2k"
        self.input = Cp2kInput()
        
        self._executable_activate(enforce=True) #这里激活executable倒是可以正常进行，因为包里有了cp2k/... 模块
     


    # adding pickle implements to special job, it might a wrong place
    def __reduce__(self, ):

        from pyiron import pyiron_to_ase

        #removed self._server
        return (self._unpickle_J, (
                                self.project.path, self.job_name, pyiron_to_ase(self._structure),\
                                    self.input, self._executable,\
                                    self.restart_file_list, self._compress_by_default, )
                )

    @classmethod
    def _unpickle_J(cls, project_path, job_name, structure, job_input, job_exec, job_restart_file_list, job_compress_flag):

        from pyiron import ase_to_pyiron

        pr = Project(project_path) #we cant just copy project for the job_type unpickable
        #job = cls(project=pr, job_name=job_name)
        job = pr.create_job(job_type=cls, job_name=job_name)
        job.structure = ase_to_pyiron(structure)
        job.input = job_input
        #job._server = job_server # _runmode unpickle, removed

        job._executable = job_exec #not for pyiron_base job?
        job.restart_file_list = job_restart_file_list
        job.compress_by_default = job_compress_flag

        return job

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
        self._write_cp2k_cell()
    
    def _revise_walltime_by_run_time(self):
        # revise walltime for elegant quit in cp2k program
        
        if self.server.run_time:
            self.input.control.GLOBAL["WALLTIME"] = \
                self.server.run_time-200
            assert int(self.input.control.GLOBAL["WALLTIME"]) > 0
        
    
    def _write_cp2k_input(self):
        
        input = self.input.render_dict()
        cell_info = as_dict_from_struct(self.structure)
        merge_dict(input, cell_info)
        final_input = dict2inp(input, mode=self.input.parser)
        
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


    # restart implements for unfinished MD tasks
    # the restart job result will be merged to the "master" job
    def _restart_cp2k_job(self, job_name=None, job_type=None):
        
        #定义原任务作为src job
        # restart job和src job是主从关系
        # 结果是否汇总到 原job 中？
        
        # pyiron-pos-* 类结果应该如何处理？ 理论上应该是连续的
        # 多个restart任务的波函数如何处理
        # 
        
        # 1. 确定restart_file_list哪些是要复制的
        ## .restart文件（包含位置信息？）
        ## pyiron-RESTART.wfn* 文件
        ## 

        # 这里的结构是没有用的，只是为了满足pyiron架构

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
        new_ham.input.control["EXT_RESTART"] = {}
        new_ham.input.control["EXT_RESTART"]["RESTART_FILE_NAME"] = "./pyiron-1.restart"
        #重新设置 任务的counters
        #new_ham.input.control["EXT_RESTART"]["RESTART_COUNTERS"] = True


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
        new_ham.input.control["FORCE_EVAL"]["DFT"]["WFN_RESTART_FILE_NAME"] = './pyiron-RESTART.wfn'
        new_ham.input.control["FORCE_EVAL"]["DFT"]["SCF"]["SCF_GUESS"] = "RESTART"
            
        return new_ham


    #restart 的实现
    def read_restart_file(self):

        # 参考lammpsbase
        #                
        pass


    def restart(self, job_name=None, job_type=None):
        
        #这里抄的lammps的方法
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



    # def write_psf_files():

    #     pass
    
    # #仅支持nvt
    # def _get_structure(self, frame=-1, wrap_atoms=False):
        
    #     warnings.warn("not support to wrap atoms")
        
    #     snapshot = Atoms(
    #         elements=self.structure.elements,
    #         positions=self._xyz_universe.trajectory[frame].positions,
    #         cell=self.structure.cell,
    #         pbc=self.structure.pbc,
    #     )

    #     return snapshot


    # def _number_of_structures(self):

    #     # xyzfile = self["output/generic"]["xyz_filename"]
    #     # xyzfile = self.job_file_name(xyzfile)
    #     # u = Universe(xyzfile)

    #     return len(self._xyz_universe.trajectory)

    def collect_xyz_file(self, file_pattern="pyiron-pos-1.xyz", cwd=None):

        files = list(Path(self.job_file_name(file_name="", cwd=cwd)).glob(file_pattern))
        if not files:
            warnings.warn(f"CP2K warning: No {file_pattern} output file found.")
            return 

        file_name = files[0].name #只处理pos-1.xyz

        with self.project_hdf5.open("output/generic") as hdf_output:
            hdf_output["xyz_filename"] = file_name

    
        pass

    # def collect_cube_file():
    #     pass

    # def collect_pdos_file():

    #     pass


    def collect_output(self):

        self.collect_xyz_file(file_pattern="pyiron-pos-1.xyz", cwd=self.working_directory)
        # self._xyz_universe = Universe(self.job_file_name("pyiron-pos-1.xyz")) #有pickle无法复原的问题

        self.input.from_hdf(self._hdf5)

        #TODO collect 接口需要继续做
        # if os.path.isfile(
        #     self.job_file_name(file_name="dump.h5", cwd=self.working_directory)
        # ):
        #     self.collect_h5md_file(file_name="dump.h5", cwd=self.working_directory)
        # else:
        #     self.collect_dump_file(file_name="dump.out", cwd=self.working_directory)
        
        # self.collect_output_log(file_name="log.lammps", cwd=self.working_directory)
        # if len(self.output.cells) > 0:
        #     final_structure = self.get_structure(iteration_step=-1)
        #     if final_structure is not None:
        #         with self.project_hdf5.open("output") as hdf_output:
        #             final_structure.to_hdf(hdf_output)

    ##2022.10.4补充
    def view_cp2k_job_structure(self, ):

        #使用mda读取轨迹, 避免速度过慢
        from MDAnalysis import Universe
        from ase import Atoms
        import nglview as nv
        
        posfile = self.job_file_name("pyiron-pos-1.xyz")
        uni = Universe(posfile)
        print(len(uni.trajectory))
        return nv.show_mdanalysis(uni)
        #return uni

    def get_cp2k_job_final_frame(self, pbc=True):
        #使用mda读取轨迹, 避免速度过慢
        from MDAnalysis import Universe
        from ase import Atoms
        
        posfile = self.job_file_name("pyiron-pos-1.xyz")
        uni = Universe(posfile)
        
        return Atoms(
            uni.atoms.elements, 
            positions=uni.trajectory[-1].positions,
            cell = self.structure.cell,
            pbc=pbc
        )

    ## 2022.10.4补充结束，这里的注释最好删去



class Cp2kInput():
    
    def __init__(self, ff_type="DFT", parser="local"):
        
        #TODO:
        # 以后拆分成:
        # 1. mainpage(没想好名字) 进行主要的关键词的存储
        # 2. global: global有关时间墙和其他的存储
        # 3. control 一些快捷定义任务的方法的实现
        # 4. 其他已经well defined的模块可以继续从mainpage中抽出来做对象处理
        
        
        self.control = Cp2kControl(table_name="cp2k_control")
        self.kind = kind_dict[ff_type](table_name="cp2k_kind")

        self.parser=parser
        #psf文件应该怎么输出和导入，这是个问题
    
    def from_input_file(self, input_filename, *fargs, **fkwargs):
        

        input_dict = inp2dict(input_filename, mode=self.parser, *fargs, **fkwargs)
 
        ff_type = choose_ff_type(input_dict)
        kindclass = kind_dict[ff_type]

        self.control = Cp2kControl.from_input_dict(input_dict, table_name="cp2k_control")
        self.control._init_control()
        self.kind = kindclass.from_input_dict(input_dict, table_name="cp2k_kind")

    

    def render_dict(self):
        
        total = {}
        #merge有指针问题
        merge_dict(total, self.control.as_input_dict_part())
        merge_dict(total, self.kind.as_input_dict_part())

        return total
    
    def render_input_dict(self):

        inp = self.render_dict()

        return dict2inp(inp, mode=self.parser)
    
    def preview(self,):
        
        txt = self.render_input_dict()
        print(txt)
        
    def to_hdf(self, hdf):
        """
        datacontainer对hdf的实现, 任务信息的保存过程
        """
        with hdf.open("input") as hdf5_input:
            self.control.to_hdf(hdf5_input,"control")
            self.kind.to_hdf(hdf5_input,"kind")

    def from_hdf(self, hdf):
        """
        datacontainer对hdf的实现, 任务信息的恢复过程
        """
        with hdf.open("input") as hdf5_input:
            self.control.from_hdf(hdf5_input,"control")
            self.kind.from_hdf(hdf5_input,"kind")
            
            
    def visualize_md(self):
        
        #actually loading the *.xyz file to nglview
        #in remote, it will be complex for file stream transfer?
        pass
        
    
