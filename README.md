# pyiron_ecbeta
Here is a pyiron_atomistics based CP2K software interface.

You can use it in a Pyironic Style for submitting CP2K calculation. 


Example to create a CP2K job.

```py
#import some necessary package
import ase.io as io
import numpy as np
from pyiron import Project, ase_to_pyiron
from pyiron_echem.cp2k.cp2k import Cp2kJob

work_path = "test_cp2k"
pr = Project(work_path)


file_struct = "./your_structure.xyz"
file_template = "./your_cp2k.inp"

# define detaild strucure information by ase.Atoms
# cell and pbc info will be used in jobs
struct = io.read(file_struct)
struct.cell = [10.139,  10.139,  32.169 ]
struct.pbc = True

#create CP2K job by pyiron
calc_name = "untitled"
calc = pr.create_job(Cp2kJob, job_name=calc_name)

calc.structure = ase_to_pyiron(struct) 
calc.input.from_input_file(file_template) #import the input temaple

#submit pyiron cp2k job
calc.server.queue = "your_hpc_queue" #check pyiron_base to define the queue
calc.run()



#also you can edit the input content like this
# such as
#_content = calc.input.content
#_content.FORCE_EVAL.DFT.MGRID.CUTOFF==400
# and preview input
# calc.input.preview()

# check the task process like this 
# calc.view.tail_file("cp2k_output")
# calc.view.view_cp2k_structure()


```