__version__ = "0.0.1"


from pyiron_base import JOB_CLASS_DICT

# Make classes available for new pyiron version
JOB_CLASS_DICT['Cp2kJob'] = 'pyiron_ecbeta.cp2k.cp2k'
JOB_CLASS_DICT['Vasplite'] = 'pyiron_ecbeta.vasplite.vasplite'
