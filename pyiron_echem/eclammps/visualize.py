from ipywidgets import Dropdown, FloatSlider, IntSlider, HBox, VBox, Text, interactive, IntText,Label, Tab, Button

from nglview.widget import NGLWidget
from nglview import MDAnalysisTrajectory
from MDAnalysis.transformations import wrap as trans_wrap
import nglview as nv
import nglview.color
import os
from pyiron_base.state import state
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


#FIXME: ugly
from ..cp2k.visualize import ECViewer


#copied and modified from miko-analyzer: read_model_deviation in github
def get_model_deviation_df(model_devi_path: Path):
    model_devi_path = model_devi_path.resolve()
    try:
        
        #TODO: model_devi 输出的header会与dp势的版本有关
        meta = np.loadtxt(model_devi_path)
    except FileNotFoundError as err:
        print(f'file: {model_devi_path} not found')
        raise err
    #TODO: 直接把数组变成dataframe
    return pd.DataFrame({
        "steps": meta[:,0],
        "max_devi_v" : meta[:,1],
        "min_devi_v" : meta[:,2],
        "avg_devi_v" : meta[:,3],
        "max_devi_f" : meta[:,4],
        "min_devi_f" : meta[:,5],
        "avg_devi_f" : meta[:,6],
    })



def plot_model_devi_timestep(ax, df_model_devi, model_devi_type="max_devi_f", trust_low=None, trust_high=None,):


    model_devi = df_model_devi
    #ax = axs[0]
    plot_item = model_devi_type
    label_unit = ""

    sns.scatterplot(model_devi[model_devi_type], alpha=0.5, ax=ax, label=f'{plot_item} {label_unit}')

    if trust_low is not None:
        ax.axhline(trust_low, linestyle='dashed')
    if trust_high is not None:
        ax.axhline(trust_high, linestyle='dashed')
    if ax.get_subplotspec().is_last_row(): # type: ignore
        ax.set_xlabel('Simulation Steps')
    if ax.get_subplotspec().is_first_col(): # type: ignore
        #ax.set_ylabel(r'$\sigma_{f}^{max}$ (ev/Å)')
        ax.set_ylabel(r'$\sigma_{f}$ (eV/Å)')
    ax.legend(loc="upper right")
    ax.set_ylim([-0.02, 1.1])
    
    return ax

def plot_model_devi_distribution(ax, df_model_devi, model_devi_type="max_devi_f", trust_low=None, trust_high=None):
    
    label = "unknown label"
    orientation = "vertical"
    # draw the kernel density estimate plot
    if orientation == 'vertical':
        sns.kdeplot(y=df_model_devi[model_devi_type], label=label, fill=True, alpha=0.5, ax=ax)
        if trust_low is not None:
            ax.axhline(trust_low, linestyle='dashed')
        if trust_high is not None:
            ax.axhline(trust_high, linestyle='dashed')
    
    #ax.set_yticks(False)
    ax.set_ylabel('')
    ax.tick_params(labelleft=False)
    ax.set_ylim([-0.02, 1.1])

    #ax.legend() #show label
    return ax

def get_lammps_ener_df(ener_filename):
    
    return pd.read_table(ener_filename, sep="\s+", header=0)
    

class ECLammpsView():
    
    def __init__(self, job):
        
        self._job = job
        self._logger = state.logger
    
    def get_ener(self, ener_filename="ener.out"):
        
        return get_lammps_ener_df(self._job.job_file_name(ener_filename))
    
    def view_ener(self, types=["Temp","TotEng", "PotEng","KinEng",], ener_filename="ener.out", output=False):
        
        
        if type(types) == str:
            types = [types]
        #init plt rcparam
        # TODO: it is global ,check it after
        # plt.rc('font', size=18)
        # plt.rc('axes', titlesize=23)
        # plt.rc('axes', labelsize=20) 
        # plt.rc('xtick', labelsize=12) 
        # plt.rc('ytick', labelsize=12) 
        # plt.rc('legend', fontsize=16)

        # plt.rc('lines', linewidth=2, markersize=10) #controls default text size

        # plt.rc('axes', linewidth=2)
        # plt.rc('xtick.major', size=10, width=2)
        # plt.rc('ytick.major', size=10, width=2)
        # plt.rc('axes.formatter', useoffset=False)

        df =self.get_ener(ener_filename)
        row = len(types)
        col = 1#
        fig = plt.figure(figsize=(9*col,4*row), dpi=150, facecolor='white')#

        n_graphs = row*col#
        gs = fig.add_gridspec(row,col)#
        axes  = [fig.add_subplot(gs[i]) for i in range(n_graphs)]

        for i in range(n_graphs):
            sns.lineplot(df[types[i]], ax=axes[i])
        
        fig.show()
        if output:
            fig.savefig(self._job.job_file_name("ener.pdf"), dpi=400)
    
        return fig
    
    def get_model_devi(self, model_devi_filename="model_devi.out"):
        
        return get_model_deviation_df(
            Path(self._job.job_file_name(model_devi_filename))
            )
    
    def view_model_devi(self, model_devi_filename="model_devi.out",
                        model_devi_type="max_devi_f", 
                        trust_low=None, 
                        trust_high=None,
                        show_distribution=True,
                        ):
        
        model_devi = self.get_model_devi(model_devi_filename=model_devi_filename)
        
        fig = plt.figure(figsize=(9,3), dpi=150, facecolor='white',)#
        gs = fig.add_gridspec(9,4)
        ax_md = plt.subplot(gs[:, :3])
        
        
        plot_model_devi_timestep(ax_md, model_devi, model_devi_type=model_devi_type, trust_low=trust_low, trust_high=trust_high)
        if show_distribution:
            ax_dis = plt.subplot(gs[:, 3:], sharey=ax_md)
            plot_model_devi_distribution(ax_dis, model_devi, model_devi_type=model_devi_type, trust_low=trust_low, trust_high=trust_high)
        
        return fig
        
    def view_frames(self, wrap=True, traj_filename="traj.xyz", **ukwargs):
        
        return self.view_lammps_job_structure(wrap=wrap, traj_filename=traj_filename, **ukwargs)        
    
    
    def view_lammps_job_structure(self, wrap=True, traj_filename="traj.xyz", **ukwargs):
        
        #导入轨迹的方法都很类似
        #TODO: 将来支持lammpstrj格式
        
        #using MDA to loading the traj
        from MDAnalysis import Universe
        import nglview as nv
        
        posfile = self._job.job_file_name(traj_filename)
        uni = Universe(posfile, **ukwargs)
        print(len(uni.trajectory))
        
        if wrap==True:
            ag = uni.atoms
            transform = trans_wrap(ag)
            uni.dimensions = self._job.structure.cell.cellpar()
            uni.trajectory.add_transformations(transform)
        
        #TODO: using uni.dimensions to wrap traj
        
        gui = ECViewer(uni).gui
        #return uni
        #view = nv.show_mdanalysis(uni)
        
        show_arrow = True
        if show_arrow == True:
            gui.view.shape.add_arrow([-2, -2, -2], [2, -2, -2], [1, 0, 0], 0.5)
            gui.view.shape.add_arrow([-2, -2, -2], [-2, 2, -2], [0, 1, 0], 0.5)
            gui.view.shape.add_arrow([-2, -2, -2], [-2, -2, 2], [0, 0, 1], 0.5)        
        
        # view.camera = 'orthographic'
        #return view
        return gui
