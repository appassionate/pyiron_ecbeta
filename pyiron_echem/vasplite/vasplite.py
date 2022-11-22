
import numpy as np
from pyiron_atomistics.vasp.vasp import Vasp
from pyiron_atomistics.vasp.base import VaspCollectError


# the original vasp class will be heavy to do the postprocessing work
# in our routine, now, we have less using in those result, so to lite the vasp job will be neccessary 
# it is why Vasplite matters
class Vasplite(Vasp):

    def __init__(self, project, job_name):
        super(Vasplite, self).__init__(project, job_name)

        self.__version__ = (
            None  # Reset the version number to the executable is set automatically
        )
        self._compress_by_default =False
        # 当前版本Vasp 的压缩选项有问题， 选择直接设置为fasle,避免重新序列化时自动压缩
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