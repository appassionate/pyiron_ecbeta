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


def batch_run_job_lst(jobs, onqueue_num=4, exec_name=None, queue=None, interval=20, **runkwargs):
    """
    trying to limit the jobs on the queue.
    """
    
    
    #jobs = list(filter(lambda job: job.status=="initialized", jobs))
    submitted_jobs = []
    end_status = ["finished","aborted","suspended"]
    cur_idx = 0

    for job in jobs[cur_idx: cur_idx+onqueue_num]:
        cur_job = jobs[cur_idx]
        submit_job(job, exec_name, queue, **runkwargs)
        submitted_jobs.append(cur_job)
        cur_idx+=1
    
    while jobs[cur_idx:]:
        #remote状态下status刷新会有问题吗？需要测试 TODO
        num_on_queue = sum([job.status not in end_status for job in submitted_jobs])
        added_num = onqueue_num - num_on_queue
        for job in jobs[cur_idx:cur_idx+added_num]:
            cur_job = jobs[cur_idx]
            submit_job(job, exec_name, queue, **runkwargs)
            submitted_jobs.append(cur_job)
            print("submit job: " ,cur_job.job_name ,"cur_pr: ",cur_job.project)
            cur_idx+=1
            
        if not added_num:
            time.sleep(interval)
    
    last_queue = list(filter(lambda job: job.status not in end_status, submitted_jobs))
    if not last_queue:
        return submitted_jobs
    #用最后一个提交任务的状态 来作为 全部任务是否都运行了的依据
    last = last_queue[-1]
    last.project.wait_for_job(last,interval_in_s=interval, max_iterations=5000)
    
    return submitted_jobs


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
    # 更新database
    # 任务状态重置为initialized
    # input 重置为？ 要检查 save会覆盖原
    
    job.status._reset()
    job._status._status_dict["initialized"] = True
    job.status.database.set_job_status(job.job_id, 'created')
    
    # 启用 pyiron-1.restart
    job.input.control["EXT_RESTART"] = {}
    job.input.control["EXT_RESTART"]["RESTART_FILE_NAME"] = "./pyiron-1.restart"
    
    #启用wfn restart
    # using pyiron-1.restart in restart_job.input
    if use_wfn:
        job.input.control["FORCE_EVAL"]["DFT"]["WFN_RESTART_FILE_NAME"] = './pyiron-RESTART.wfn'
        job.input.control["FORCE_EVAL"]["DFT"]["SCF"]["SCF_GUESS"] = "RESTART"
    
    # 更新Input 文件， 也许需要增加备份的方法
    job.write_input()
    #job save时候会更新Input文件!
    #job.save()
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