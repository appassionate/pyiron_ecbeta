from .cp2k import cp2k2inp, cp2k2dict
from .local import local2inp, local2dict



def dict2inp(input_dict, mode='local', *fargs, **fkwargs):


    if mode =='local':
        writefunc = local2inp
    else:
        writefunc = cp2k2inp

    
    return writefunc(input_dict)


def inp2dict(filename, mode='local',  *fargs, **fkwargs):

    #pass
    if mode == "cp2k":
        parserfunc=cp2k2dict
    else:
        parserfunc=local2dict

    return parserfunc(filename, *fargs, **fkwargs)
