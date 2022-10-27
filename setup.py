import setuptools

#with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="pyiron_echem",
    version="0.0.1",
    author="Ke Xiong",
    author_email="xiongke@stu.xmu.edu.cn",
    description= "pyiron based implements in ChengLab",
#    long_description=long_description,
    long_description_content_type="text/markdown",
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
        "pyiron_atomistics==0.2.47"
  ]
#    entry_points={
#        'console_scripts': [
#            'tlk=toolkit.main:cpdat']
#        }
)
