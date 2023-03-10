
import numpy as np
from pyiron import Project
from pyiron_atomistics.vasp.vasp import Vasp
from pyiron_atomistics.vasp.base import VaspCollectError


# the original vasp class will be heavy to do the postprocessing work
# in our routine, now, we have less using in those result, so to lite the vasp job will be neccessary 
# it is why Vasplite matters
class Vasplite(Vasp):

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

    def __init__(self, project, job_name):
        super(Vasplite, self).__init__(project, job_name)

        self.__version__ = (
            None  # Reset the version number to the executable is set automatically
        )
        self._compress_by_default =False
        #self._executable_activate(enforce=True)
        self._executable_activate(enforce=True,codename="vasp")

    def collect_output(self):
    
        """
        only do some structure saving in hdf5 files
        """
        if self.structure is None or len(self.structure) == 0:
            try:
                self.structure = self.get_final_structure_from_file(filename="CONTCAR")
            except IOError:
                self.structure = self.get_final_structure_from_file(filename="POSCAR")
            self._sorted_indices = np.array(range(len(self.structure)))
        self._output_parser.structure = self.structure.copy()
        try:
            self._output_parser.collect(
                directory=self.working_directory, sorted_indices=self.sorted_indices
            )
        except VaspCollectError:
            self.status.aborted = True
            return
        # Try getting high precision positions from CONTCAR
        try:
            self._output_parser.structure = self.get_final_structure_from_file(
                filename="CONTCAR"
            )
        except (IOError, ValueError, FileNotFoundError):
            pass
    
    def convergence_check(self):
        # do do convergence check
        # return True to asssgin the job is finished 
        
        #TODO: more simple convergence check for some label using 
        
        return True