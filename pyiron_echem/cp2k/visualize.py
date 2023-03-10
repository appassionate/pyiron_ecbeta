from ipywidgets import Dropdown, FloatSlider, IntSlider, HBox, VBox, Text, interactive, IntText,Label, Tab, Button

from nglview.widget import NGLWidget
from nglview import MDAnalysisTrajectory
import nglview.color
import os
from pyiron_base.state import state



class Cp2kView():
    
    def __init__(self, job):
        
        self._job = job
        self._logger = state.logger

    def view_cp2k_job_structure(self, ):

        #using MDA to loading the traj
        from MDAnalysis import Universe
        import nglview as nv
        
        posfile = self._job.job_file_name("pyiron-pos-1.xyz")
        uni = Universe(posfile)
        print(len(uni.trajectory))
        
        #TODO: using uni.dimensions to wrap traj
        
        return ECViewer(uni).gui
        #return uni

    def tail_file(self, filename="output", n=10):
        # only linux, 
        filename = self._job.job_file_name(filename)
        command = "tail -n {0} {1}".format(n, filename)
        with os.popen(command) as pipe:
            last_lines = pipe.read()
        print(last_lines)
        #return last_lines

    def view_cp2k_pdos(self, kind="k1", spin=None, orbitals=["1s", "2s", "2p", "3s", "3p", "3d"], ):
        pass


class ECViewer():
    
    
    def __init__(self, atoms, xsize= 400, ysize= 300):
        
        
        #process "atoms"
        ## first mda.atoms
        self._trajectory = atoms
        self.elements = atoms.universe.atoms.elements
        
        #prepare for detailed view in ngl
        self.short_frame_range = None
        self.complete_frame_range = None
        
        self._init_view(xsize, ysize) #initialize a widget
        self.set_wdg_gui()
        
        #self.widgets = _init_wdgets()  #?????????????? #some tools
        #self.widgets.get('?').observe(self._refresh_radius)
        
        
        #self.show_colorbar(data) #external data we need to repr
        
    def _init_view(self, xsize, ysize):
        
        
        self.view = NGLWidget(gui=False)  #or show_ase?
        
        self.view.add_trajectory(MDAnalysisTrajectory(self._trajectory))
        
        #view.clear_representations()
        
        self.colors = {} #for chose use
        self._resize_widget(xsize, ysize)
        self.view.camera = 'orthographic'
        self.parameters = {"clipDist": 0}
        self.view.add_unitcell()   
        self.view.add_spacefill() 
        self.view.update_spacefill(
                    radiusScale=0.43
                )        
    
    def set_wdg_gui(self):
         
        #init
        #frame select should be designed as a buttom input param
        #self.frm_sel_slider = IntSlider(value=0, min=0, max=len(ag.universe.trajectory) - 1) #it will be some slider in it  or maybe frm list
        
        #some style 
        self.slider_style = {'description_width': 'initial'}
        self.drop_style = {'description_width': 'initial'}
        #some layout
        #self.slider_layout = Layout(width='30%', height='12px')
        #self.drop_layout = Layout(width='30%', height='12px')
        
        ### frame section ###
        self.frm_sel_slider = IntSlider(value=0, min=0, max=len(self._trajectory.universe.trajectory),  style=self.slider_style, )
        self.frm_play_velo_slider = IntSlider(value=4, min=1, max=10, description='velocity: ', style=self.slider_style,)
        

        self.rad_sel_slider = FloatSlider(value=0.43, min=0.0, max=1.5, step=0.02, description='Atom Size:', style=self.slider_style)  
        self.e_sel_drop = Dropdown(options=['All'] +
                             list(set(self.elements)),
                             value='All', description='Element Show:',  style=self.drop_style)
        
        #currently, only element is meanningful, we should have more representations in this factor
        self.c_sel_drop = Dropdown(options=['  ','element'],
                             value='element', description='Color Scheme:', style=self.drop_style)
        self.camera_sel_drop = Dropdown(options=['perspective', 'orthographic'],
                             value='orthographic', description='Camera: ', style=self.drop_style)
        
        
        self.frm_sel_slider.observe(self._update_frame)
        self.frm_play_velo_slider.observe(self._update_frame_velocity)
        self.e_sel_drop.observe(self._select_atom)
        #self.c_sel_drop.observe(self._update_color_scheme)##################
        self.rad_sel_slider.observe(self._update_radius)
        self.camera_sel_drop.observe(self._update_camera_type)
        
        wdg_block = [self.e_sel_drop, self.c_sel_drop, self.rad_sel_slider, self.camera_sel_drop]
        frame_block = [Label('Frame:'),self.frm_sel_slider, self.frm_play_velo_slider,]#######
        
        self.gui = VBox([self.view, HBox([VBox(wdg_block), VBox(frame_block)])])
        self.gui.view = self.view#???what mean
        self.gui.control_box = self.gui.children[1]#?

    def _update_radius(self, chg=None):## maybe more input para
        
        self.view.update_spacefill(
                    radiusScale=self.rad_sel_slider.value
                )
    def _update_atom_type(self, chg=None):
        #what chg will be used
        
        #radius, coordinate or others
        # we can develop a drop to select it.
        self.view.update_spacefill(
            radiusType='coordinate'
        )
        pass
    
    def _update_frame_velocity(self, chg=None):
        
        self.view.player.delay = 1/(self.frm_play_velo_slider.value*0.005)+0.05
        pass
    
    def _update_color_scheme(self, chg=None):
        self.view.update_spacefill(
            color_scheme=self.c_sel_drop.value,
            color_scale='rainbow')

    def _update_frame(self, chg=None):
        self.view.frame = self.frm_sel_slider.value
        return

    def _select_atom(self, chg=None):
        
        sel = self.e_sel_drop.value
        self.view.remove_spacefill()
        self.view.clear_representations()
        for e in set(self.elements):
            if (sel == 'All' or e == sel):
                if e in self.colors:
                    self.view.add_spacefill(selection='#' + e,
                                            color=self.colors[e])
                else:
                    self.view.add_spacefill(selection='#' + e)
                    
        self._update_color_scheme()
        self._update_atom_type()
        self._update_radius()

        
    
    def _update_camera_type(self, camera_type):
        
        self.view.camera=self.camera_sel_drop.value
        
    def _resize_widget(self, xsize, ysize):
        
        self.view._remote_call('setSize', target='Widget',
                               args=['%dpx' % (xsize,), '%dpx' % (ysize,)]) 