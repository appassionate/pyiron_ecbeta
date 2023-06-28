# TODO:  copyright is need.
import random
import numpy as np
from pyiron_atomistics.lammps.interactive import LammpsInteractive
from pyiron_atomistics.lammps.lammps import Lammps
from pyiron_atomistics.lammps.base import Input as LammpsInput
from pyiron_atomistics.lammps.control import LammpsControl



from pyiron_base.state import state
from pyiron_echem.eclammps.potential import ECLammpsPotential 
from pyiron_echem.eclammps.utils import collect_model_devi
from pyiron_echem.eclammps.visualize import ECLammpsView


# EClammps aims to reduce the collect process in 
# original pyiron_atomistics and add more implementations of dpmdkit model using

class ECLammps(Lammps):
    
    
    def __init__(self, project, job_name):
        
        super(Lammps, self).__init__(project, job_name)
        self.__name__ = "lammps"
        self._executable_activate(enforce=True,codename="lammps")
        
        self.input = ECLammpsInput() # just override it..
        
        self.input.control._block_dict["environment"] = \
        tuple((list(self.input.control._block_dict["environment"]) + ["box"]))
        #有bug 貌似不能改变read_file的顺序 box_**到底属于哪一类？
        self.input.control._block_dict["structure"] = \
        tuple((list(self.input.control._block_dict["structure"]) + ["change_box"]))
        
        self.view = ECLammpsView(self)
        self._compress_by_default = False
    
    
    def collect_output(self):
        
        self.input.from_hdf(self._hdf5)
        #TODO: skipped collecting, we less use it.
        # skip traj process and big data process    
        
    def convergence_check(self):
        
        
        self._logger.info("ECLammps will not do converge check, return True.")
        return True

    def get_frame(self, index=-1, pbc=True, traj_filename="traj.xyz"):
        #dump? lammpstraj?
        
        #使用mda读取轨迹, 避免速度过慢
        from MDAnalysis import Universe
        from ase import Atoms
        
        posfile = self.job_file_name(traj_filename)
        uni = Universe(posfile)
        
        return Atoms(
            uni.atoms.elements, 
            positions=uni.trajectory[index].positions,
            cell = self.structure.cell,
            pbc=pbc
        )

    def write_input(self):
        """
        Call routines that generate the code specific input files

        Returns:

        """
        
        if self.structure is None:
            raise ValueError("Input structure not set. Use method set_structure()")
        lmp_structure = self._get_lammps_structure(
            structure=self.structure, cutoff_radius=self.cutoff_radius
        )
        lmp_structure.write_file(file_name="structure.inp", cwd=self.working_directory)
        version_int_lst = self._get_executable_version_number()
        update_input_hdf5 = False
        if (
            version_int_lst is not None
            and "dump_modify" in self.input.control._dataset["Parameter"]
            and (
                version_int_lst[0] < 2016
                or (version_int_lst[0] == 2016 and version_int_lst[1] < 11)
            )
        ):
            self.input.control["dump_modify"] = self.input.control[
                "dump_modify"
            ].replace(" line ", " ")
            update_input_hdf5 = True
        if not all(self.structure.pbc):
            self.input.control["boundary"] = " ".join(
                ["p" if coord else "f" for coord in self.structure.pbc]
            )
            update_input_hdf5 = True
        self._set_selective_dynamics()
        if update_input_hdf5:
            self.input.to_hdf(self._hdf5)
        self.input.control.write_file(
            file_name="control.inp", cwd=self.working_directory
        )
        self.input.potential.write_file(
            file_name="potential.inp", cwd=self.working_directory
        )
        
        if self.input.potential._enable_copy:
            
            if self.input.potential._symlink_by_default:
                self.input.potential.symlink_pot_files(self.working_directory)
            else:
                self.input.potential.copy_pot_files(self.working_directory)
    
    def _do_some_control_init(self,):
        
        self.calc_md() #以后最好不要调用这个
        del self.input.control["dimension"] #删除多余的dimension command 
        del self.input.control["fix___ensemble"] #删除自带的fix ensemble, 需要再添加 
        del self.input.control["velocity"] #删除初始速度的设置 之后再添加，有随机种子的问题
        del self.input.control["variable___thermotime"]  #删除热力学相关的设置 之后再添加
        del self.input.control["thermo"]
        del self.input.control["thermo_style"]
        del self.input.control["thermo_modify"]

    def calc_dpmd(self,
             ensemble="nvt",
             nsteps=20000,
             dt=0.0005,
             traj_freq=10,
             temp=300, 
             mass_map=None, #根据type_map 即势能顺序设置
             pres=-1, # 无效参数 
             tau_t=0.1,  #nvt 系综下的参数
             tau_p=0.5, # 无效参数
             max_seed=1000000,
             neighbor=2.0,
             dump_lammpstrj=True,
             dump_xyz=True):
        #thermo_freq = dump_freq(xyz file)
    
        #1. 删除默认的多余control command
        self._do_some_control_init()
        
        #command: box相关补全a
        #BUG box 的定义要放在run之前,意味这我们要对control dataframe手动排序
        #dpmd中存在的box command, pyiron暂时没有预定义
        self.input.control["box"] = "tilt large" 
        self.input.control["change_box"] = "all triclinic"
        #2. dpmd相关参数补全
        #为了和dpmd保持一致，补全一下variable的定义
        self.input.control["variable___NSTEPS"] = "equal  "+ str(nsteps)
        self.input.control["variable___THERMO_FREQ"] = "equal  "+ str(traj_freq)
        self.input.control["variable___DUMP_FREQ"] = "equal  "+ str(traj_freq)
        self.input.control["variable___TEMP"] = "equal  "+ str(temp)
        self.input.control["variable___PRES"] = "equal  "+ str(pres)
        self.input.control["variable___TAU_T"] = "equal  "+ str(tau_t)
        self.input.control["variable___TAU_P"] = "equal  "+ str(tau_p)
        
        #command: run, timestep运行步数,步长补全(ionic steps)
        self.input.control["run"] = "${NSTEPS}"
        self.input.control["timestep"] = dt
        
        #command: neighbor 相关补全
        self.input.control["neighbor"] = str(neighbor)+" bin"
        self.input.control["neigh_modify"] = "every 1"  

        #command: fix 系综相关参数补全
        # copied from ai2-kit.domain.lammps
        no_pbc = np.any(self.structure.pbc)
        if ensemble=="nvt":
            fix_1_value = 'all nvt temp ${TEMP} ${TEMP} ${TAU_T}'
        if ensemble.startswith('npt') and no_pbc:
            raise ValueError('ensemble npt conflict with no_pbc')
        if ensemble in ('npt', 'npt-i', 'npt-iso',):
            fix_1_value = 'all npt temp ${TEMP} ${TEMP} ${TAU_T} iso ${PRES} ${PRES} ${TAU_P}'
        elif ensemble in ('npt-a', 'npt-aniso',):
            fix_1_value = 'all npt temp ${TEMP} ${TEMP} ${TAU_T} aniso ${PRES} ${PRES} ${TAU_P}'
        elif ensemble in ('npt-t', 'npt-tri',):
            fix_1_value = 'all npt temp ${TEMP} ${TEMP} ${TAU_T} tri ${PRES} ${PRES} ${TAU_P}'
        elif ensemble in ('nvt',):
            fix_1_value = 'all nvt temp ${TEMP} ${TEMP} ${TAU_T}'
        elif ensemble in ('nve',):
            fix_1_value = 'all nve'
        self.input.control["fix___1"] = fix_1_value
        
        
        #command: velocity 初始速度相关参数补全
        self.input.control["velocity"] = "all create ${TEMP} %d \n" % (random.randrange(max_seed-1)+1)
        
        #command: thermo 相关参数补全
        #job.input.control["variable___thermotime"] = 1
        del self.input.control["dump_modify___1"]
        self.input.control["thermo_style___custom"] = "step temp pe ke etotal press vol lx ly lz xy xz yz"
        self.input.control["thermo"] = "${THERMO_FREQ}"

        #输出dump.out轨迹信息部分
        self.input.control["dump___1"] = "all custom ${DUMP_FREQ} out.lammpstrj id type x y z fx fy fz"
        
        # 输出xyz轨迹部分
        # command: dump 相关参数补全, 主要为了生成xyz 轨迹, 有type_map参数的影响 根据structure 和potential对象对应拿
        if dump_xyz:
            type_map = self.potential["Species"].iloc[0] # need assert
            ele_order = " ".join(type_map)
            self.input.control["dump___TRAJ"] = "all xyz ${DUMP_FREQ} traj.xyz"
            self.input.control["dump_modify___TRAJ"] = f'element {ele_order} format line "%2s     %12.6f      %12.6f      %12.6f"'
        
        if not dump_lammpstrj: #删去原有的lammps dump词条
            del self.input.control["dump___1"]
        
        #重新调整job 的mass_map, 放在这可能不合适
        if mass_map:
            self.change_mass_map(mass_map)

        self.input.control["restart"] = "10000 ./lammps.restart"
        self.input.control["write_restart"] = "lammps.restart.final"

    def _enable_print_thermal_info(self):
        _keywords = ["step", "temp", "pe", "ke", "etotal", "press", "vol", "lx", "ly", "lz", "xy", "xz", "yz"]
        for _kw in _keywords:
            self.input.control[f"variable___{_kw}"] = f"equal {_kw}"
        self.input.control["fix___sys_info"] = 'all print ${THERMO_FREQ} "${step}    ${temp}    ${pe}    ${ke}    ${etotal}    ${press}    ${vol}    ${lx}    ${ly}    ${lz}    ${xy}    ${xz}    ${yz}" title "#Step    Temp    PotEng    KinEng    TotEng    Press    Volume    Lx    Ly    Lz    Xy    Xz    Yz" file ener.out'
    
    def calc_dpmd_long(self,
                    ensemble="nvt",
                    nsteps=4000000,
                    dt=0.0005,
                    traj_freq=10,
                    temp=300, 
                    mass_map=None, #根据type_map 即势能顺序设置
                    pres=-1, # 无效参数 
                    tau_t=0.1,  #nvt 系综下的参数
                    tau_p=0.5, # 无效参数
                    max_seed=1000000,
                    neighbor=2.0,
                    dump_lammpstrj=False,
                    dump_xyz=True):
        
        self.calc_dpmd(ensemble=ensemble,
                    nsteps=nsteps,
                    dt=dt,
                    traj_freq=traj_freq,
                    temp=temp, 
                    mass_map=mass_map, #根据type_map 即势能顺序设置
                    pres=pres, # 无效参数 
                    tau_t=tau_t,  #nvt 系综下的参数
                    tau_p=tau_p, # 无效参数
                    max_seed=max_seed,
                    neighbor=neighbor,
                    dump_lammpstrj=dump_lammpstrj,
                    dump_xyz=dump_xyz)
        self._enable_print_thermal_info()

    def calc_vdos():
        pass



    def revise_dpmd_within_plumed(self, fix_name="inplumed", plumed_filename="input.plumed"):
        
        try:
            assert f"fix___{fix_name}" not in self.input.control.keys()
        except:
            raise ValueError(f"you have determined fix_plumed command in yout input named 'fix {fix_name}'")
        
        self.input.control[f"fix___{fix_name}"] = f"all plumed plumedfile {plumed_filename} outfile output.plumed"
        
    
    def revise_dpmd_within_restrain(self, atom_i_idx, atom_j_idx, force, dist1, dist2):
        """
        detailed check in lammps fix restrain command

        Args:
            atom_i_idx (_type_): _description_
            atom_j_idx (_type_): _description_
            force (_type_): _description_
            dist1 (_type_): _description_
            dist2 (_type_): _description_
        """
        
        group_name = f"group_{atom_i_idx}_{atom_j_idx}"
        self.input.control[f"group___{group_name}"] = f"id {atom_i_idx} {atom_j_idx}"
        self.input.control[f"fix___bound___{group_name}"] = f"restrain bond {atom_i_idx} {atom_j_idx} {force} {force} {dist1} {dist2}"
        pass
    
    def calc_geoopt(self, 
                     nsteps=1,
                     trj_freq=1,
                     ener_tol=0,
                     force_tol=1.0e-3,
                     max_iter=1000,
                     max_eval=100000,
                     mass_map=None
                     ):

        #1. 删除默认的多余control command
        self._do_some_control_init()
        del self.input.control["timestep"]
        del self.input.control["run"]

        self.input.control["variable___NSTEPS"] = "equal  "+ str(nsteps)
        self.input.control["variable___THERMO_FREQ"] = "equal  "+ str(trj_freq)
        self.input.control["variable___DUMP_FREQ"] = "equal  "+ str(trj_freq)
        self.input.control["variable___FORCE_TOL"] = "equal  "+ str(force_tol)
        self.input.control["variable___ENERGY_TOL"] = "equal  "+ str(ener_tol)
        self.input.control["variable___MAX_ITER"] = "equal  "+ str(max_iter)
        self.input.control["variable___MAX_EVAL"] = "equal  "+ str(max_eval)

        self.input.control["atom_modify"] = "map yes"

        self.input.control["neighbor"] = "1.0 bin"

        self.input.control["thermo"] = "${THERMO_FREQ}"
        self.input.control["thermo_style"] = "custom step temp pe ke etotal"

        #生成xyz部分
        type_map = self.potential["Species"].iloc[0] # need assert
        eles = " ".join(type_map)
        self.input.control["dump___TRAJ"] = "all xyz ${DUMP_FREQ} traj.xyz"
        self.input.control["dump_modify___TRAJ"] = "sort id element %s"% eles  #可能有bug 要检查下
        if mass_map:
            self.change_mass_map(self, mass_map)

        self.input.control["minimize"] = "${ENERGY_TOL} ${FORCE_TOL} ${MAX_ITER} ${MAX_EVAL}"
        self.input.control["min_style"] = "cg"

    def change_mass_map(self, mass_map):
        
        # 这个方法放在structure 对象里更好
        type_map = self.potential["Species"].iloc[0] # need assert
        assert len(mass_map) == len(type_map)
        for i, mass in enumerate(mass_map):
            self.structure.get_species_objects()[i].AtomicMass = mass


# we modified pyiron_atomistics.lammps.lammps  
# Input class for a load our specified potential object
class ECLammpsInput(LammpsInput):
    
    def __init__(self):
        
        # copied from LammpsInput
        self.control = LammpsControl()
        self.potential = ECLammpsPotential()
        self.bond_dict = dict()
        # Set default bond parameters
        self._load_default_bond_params()
    
    
    #TODO: 对接lammps Plumed 插件
    
    #TODO: 添加preview, input文件所见即所得

    #TODO: 添加from_input_file 需要parser
    
    
#class ECLammpsSturcture(): 

#TODO: 是否需要把change_mass的方法迁移过来