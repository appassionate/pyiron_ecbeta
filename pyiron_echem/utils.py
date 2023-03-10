import os
import time
import shutil

import pandas as pd
from pathlib import Path

import json


def rotate_list(_list:list):

    #verfify list num
    rotated_list = []
    for i in range(len(_list)):
        tmp = _list.copy()
        tmp = [tmp[i]] + tmp[:i] + tmp[i+1:]
        rotated_list.append(tmp)
    return rotated_list


def set_available_executable(executable, pattern):
    
    ava_bins = []
    for ex in executable.list_executables():
        if pattern in ex:
            ava_bins.append(ex)
    try:
        assert ava_bins 
    except:
        raise FileNotFoundError("not found available bin, please check the bin folder")
    select_executable_version(executable, ava_bins[0])

def select_executable_version(executable, bin_name):
    
    assert bin_name in executable.list_executables()
    executable.executable_path = executable._executable_versions_list()[bin_name]



def bakup_job(job, ):
    p_pr = Path(job.project.path)
    bak_num = len(list(p_pr.glob(job.job_name+"_bak*_hdf5")))
    
    #copied_job = job.copy_to(new_job_name=job.job_name+"_bak_%04d"%bak_num)
    copied_job = job.copy_to(new_job_name="tmp_bak")
    copied_job.rename(new_job_name=job.job_name+"_bak_%04d"%bak_num)

def reset_job(job):
    
    # try to reset a job by removing
    if job.job_id:
        #self._logger.info("run repair " + str(self.job_id))
        
        master_id, parent_id = job.master_id, job.parent_id
        job_name = job.job_name
        job.remove(_protect_childs=False)
        job.reset_job_id()
        job.master_id, job.parent_id = master_id, parent_id




def submit_job(job, exec_name=None,queue=None, **runkwargs):
    
    set_available_executable(job.executable, exec_name)
    job.server.queue = queue
    job.run(**runkwargs)
    
    return job



def backup_job_file(cp2kjob, filename="output"):

    file_path = Path(cp2kjob.working_directory).joinpath(filename)
    # TODO: 是否是文件的判断
    if file_path.is_file(): 
        counter = 0
        while True :
            bk_file_path = file_path.parent.joinpath(file_path.name+".bak%03d" % counter)
            if not bk_file_path.exists(): 
                shutil.move(file_path, bk_file_path) 
                print(f"cur output: {file_path.name} has been bakup to {bk_file_path.name}")
                break
            counter += 1

def backup_job_file_by_pattern(cp2kjob, pattern):

    files = Path(cp2kjob.working_directory).glob(pattern)
    files = list(files)
    for _file in files:
        backup_job_file(cp2kjob, _file.name)


def retry_cp2k_job(job, use_wfn=True):
    
    #assert job == cp2kjob
    
    job.status._reset()
    job._status._status_dict["initialized"] = True
    job.status.database.set_job_status(job.job_id, 'created')
    
    # pyiron-1.restart
    job.input.control["EXT_RESTART"] = {}
    job.input.control["EXT_RESTART"]["RESTART_FILE_NAME"] = "./pyiron-1.restart"
    
    #wfn restart
    # using pyiron-1.restart in restart_job.input
    if use_wfn:
        job.input.control["FORCE_EVAL"]["DFT"]["WFN_RESTART_FILE_NAME"] = './pyiron-RESTART.wfn'
        job.input.control["FORCE_EVAL"]["DFT"]["SCF"]["SCF_GUESS"] = "RESTART"
    
    job.write_input()

    backup_job_file(job,"output")
    
    #check cur step to avid append step
    curstep = get_cp2k_job_md_curstep(job)

    #fix cp2k 8.2 bug
    backup_job_file_by_pattern(job, f"pyiron-v_hartree-1_{curstep}.cube")
    backup_job_file_by_pattern(job, f"pyiron-k*-1_{curstep}.pdos")
    
    return job
    

def reset_cp2k_md_step(cp2kjob, totalstep:int):
    """reset step by the target total step nums, 
    determine how many steps are need to the next calculations
    Args:
        cp2kjob (_type_): pyiron_echem cp2kjob
        totalstep (int): the target md steps you want calc to finish
    Raises:
        ValueError: _description_
    """
    #check current step and target step in restart file
    curstep = get_cp2k_job_md_curstep(cp2kjob)
    _step = totalstep - curstep
    if _step <= 0:
        raise ValueError("MD simulation seems to be finished.")
    cp2kjob.input.control.MOTION["MD"]["STEPS"] = _step
    
    print(f"setting MD steps to next: {_step} of cur: {curstep} in total: {totalstep}")
    pass

def get_cp2k_job_md_curstep(cp2k_job):
    
    ## 1. using linux shell get ener tail info
    # import subprocess 
    # ener_file = cp2k_job.job_file_name("pyiron-1.ener")
    # proc = subprocess.Popen(["tail","-n","1",f"{ener_file}"], stderr=None, stdout=subprocess.PIPE)
    # out, _ = proc.communicate()
    # curstep = int(out.split()[0])
    
    # 2. using restart file to locate current step
    _line = True
    with open(cp2k_job.job_file_name("pyiron-1.restart"), "r") as f:
        while _line:
            _line = f.readline()
            if "STEP_START_VAL" in _line:
                break
    if not _line:
        raise FileNotFoundError("STEP_START_VAL not found in this file!")
    curstep = int(_line.split()[1])
    
    return curstep
    

def check_cp2k_job_md_finished(cp2k_job, totalstep:int):
    
    if cp2k_job.input.control.GLOBAL["RUN_TYPE"] != "MD":
        raise ValueError(f"{cp2k_job.job_name} is not molecular dynamic job!")
    #check current step and target step in restart file
    curstep  = get_cp2k_job_md_curstep(cp2k_job)
    
    print(f"{cp2k_job.job_name} current step: cur: {curstep} in total: {totalstep}")
    if curstep == totalstep:
        print ("MD finished.")
        return True
    elif curstep > totalstep:
        print("MD finished, more steps are detected.")
        return True
    return False