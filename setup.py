import setuptools

#with open("README.md", "r") as fh:
#    long_description = fh.read()

#it is still named as pyiron_echem when install
setuptools.setup(
    name="pyiron_echem",
    version="0.0.1",
    author="Ke Xiong",
    author_email="xiongke@stu.xmu.edu.cn",
    description= "pyiron based implements in ChengLab",
#    long_description=long_description,
    long_description_content_type="text/markdown",
    #revise the path of the package
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
    install_requires=[
        "numpy",
        "matplotlib",
        "ase",
        "MDAnalysis>=2.0.0",
        "pyiron_atomistics==0.2.47",
        "pyiron==0.4.6",
  ]
#    entry_points={
#        'console_scripts': [
#            'tlk=toolkit.main:cpdat']
#        }
)
