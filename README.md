# pyiron_ecbeta
place pyiron_echem (beta) cp2k interface based on pyiron.


## Introduction
[need illustred]


## installization

first, such a package should be git-cloned.
git clone [here is pull]


we recommend users to create a new virtual environment in conda:
```shell
conda env create -f environment.yml
```



*revise .condarc*

```shell
vim .bashrc 
#add some GIT INIT  for pyiron ultilize revising
```

adding those texts

```shell
## add git exectuable for pyiron error ##
PATH=$PATH:/usr/bin/git
export PATH

### FOR GIT INIT ###
GIT_PYTHON_GIT_EXECUTABLE=/usr/bin/git
export GIT GIT_PYTHON_GIT_EXECUTABLE
export GIT_PYTHON_REFRESH=quiet
## pyiron error revise finished ##
```



copy pyiron files from public.data

```shell
#copy pyiron_file to home directory
cp -r /data/public.data/kxiong/pyiron_files/ ~/
#rename it
mv pyiron_files pyiron
```



setting ~/.pyiron



```
cd ~
vim .pyiron
```

it should be:

```
[DEFAULT]
FILE = ~/pyiron/pyiron.db
PROJECT_PATHS = ~/pyiron/projects
#DISABLE_DATABASE = True
RESOURCE_PATHS = ~/pyiron/resources
```

