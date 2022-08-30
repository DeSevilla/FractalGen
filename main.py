import os
import shutil
from datetime import datetime
import numpy as np
from julia import Julia, gif_julia, relative
from matplotlib import cm, colors
        

##############################################################
# Run type
##############################################################
folder = None  # an existing folder containing .pngs
# if folder is set, will remake the .gif without any simulation. if not, will run a normal simulation


##############################################################
# Display parameters
##############################################################
pixels = 1024  # pixel dimension of image. image will always be square
frames = 100  # how many frames to generate
seconds = min(1, frames / 24)
colormap = cm.inferno  # how to color the display. try cm.inferno, cm.viridis, cm.cool, cm.prism, and more!
# See https://matplotlib.org/stable/tutorials/colors/colormaps.html for more options and info
color_by_options = [
    'iterations', # color each point by how many iterations it lasted without diverging
    'diverged',   # how many iterations it took to diverge, or 0 if it didn't diverge
    'array',      # absolute value of each point (this will be the maximum value for any divergent point)
    'undiverged', # absolute value of each undivergent point, or 0 for any divergent point
    'nested'      # how many iterations it took to diverge, or absolute value if it didn't diverge
]
color_by = 'iterations'


##############################################################
# Fixed simulation parameters
##############################################################
size = 3  # size of the viewing window in the complex plane
center = 0  # center of the viewing window; must be a complex number
# center = complex(0.195, 0.245)  # another possible value; good with param at 169 degrees and radius 0.8 
point_value_max = 10  # maximum absolute value at any point


##############################################################
# Variable simulation parameters
# These can be fixed or vary by frame
##############################################################

# how many steps to run for
steps = None  # placeholder value before it's set
fixed_steps = True
if fixed_steps:
    steps = 100
else:
    steps_start = 10
    steps_end = 100



# the zoom of the window
# works by multiplying the size
zscale = None  # placeholder
fixed_zoom = True
if fixed_zoom:
    zoom = 1  # smaller values of this mean zooming out; larger values mean zooming in. avoid 0
else:
    # zoom will be linearly spaced frame-by-frame between these two values
    zoom_start = 1  # zoom at the first frame
    zoom_end = 10  # zoom at the last frame

# how much the window should be shifted, as a complex number
# works by adding to the center
shifting = None  # placeholder
fixed_shift = True
if fixed_shift:
    shifting = 0
else:
    shift_start = 0
    shift_end = complex(5, 5)

# the step equation for any point is x^p + c. this sets p
power = None  # placeholder
fixed_power = True
if fixed_power:
    power = 2  # power 
else:
    power_start = 1
    power_end = 5

# the step equation for any point is x^p + c. this sets c
param = None  # placeholder
fixed_param = True
if fixed_param:
    # you can also just set param equal to any complex number here
    param_radius = 0.8
    param_degrees = 169
else:
    # default setup traces a circle in the complex plane, this sets the range
    param_radius = 0.8
    param_degrees_center = 180
    param_degrees_range = 360
    param_degrees_start = param_degrees_center - param_degrees_range / 2
    param_degrees_end = param_degrees_center + param_degrees_range / 2

start = datetime.now()
if folder is None:
    # def _colormap_red(x): return 0.75 * np.sin((x * 5 + .25) * np.pi) + 0.67
    # def _colormap_green(x): return 0 # .55 * np.sin((x * 17 - 0.25) * np.pi) + 0.33
    # def _colormap_blue(x): return 0 # -1.1 * np.sin((x * 5) * np.pi)
    # def _colormap_green(x): return 0
    # def _colormap_blue(x): return 0
    # colormap_spec = {'red': [(0,0,0), (0.25,0,0.5),(0.75,1,1), (1,1,1)], 'green': _colormap_green, 'blue': _colormap_blue}
    # colormap = colors.LinearSegmentedColormap('custom', colormap_spec)
    # matplotlib predefined colormaps are useful here - cm.viridis, cm.ocean, cm.plasma, cm.gist_earth, etc.
    # my favorite is cm.inferno
    # try cm.prism some time, it's ugly as sin
    # the custom colormap is a prism variant (doesn't move as fast so it's somewhat less ugly but still ugly) 
    
    if fixed_steps:
        folder_steps = steps
    else:
        steps_range = steps_end - steps_start
        steps = np.linspace(steps_start, steps_end, frames)
        # steps = np.asarray([int(steps_range * (i + 1) / frames) + steps_start for i in range(frames)])
        folder_steps = steps.max()

    if zscale is None:
        if fixed_zoom:
            zscale = np.full(frames, 1 / zoom)
        else:
            zscale = np.linspace(1 / zoom_start, 1 / zoom_end, frames)

    if shifting is None:
        if not fixed_shift:
            shifting = np.linspace(shift_start, shift_end, frames)
    shifting = shifting + (1 - zoom) * center  # this keeps the zoom centered

    if param is None:
        if fixed_param:
            param = param_radius * pow(np.e, complex(0, (param_degrees / 360) * 2 * np.pi))
        else:
            arcrange = param_degrees_end - param_degrees_start
            param = np.asarray([param_radius * pow(np.e, complex(0, ((n * arcrange / frames + param_degrees_start) / 360) * 2 * np.pi)) 
                                for n in range(frames)])

    folder = relative('output', start.strftime('%Y%m%d%H%M%S') + 
                        f' {pixels}px {frames}f {size}w {folder_steps}s {param_degrees_start}-{param_degrees_end}r')
    os.makedirs(folder)
    try:
        julia = Julia(pixels, pixels, 
                    -size/2 + center.real, size/2 + center.real, -size/2 + center.imag, size/2 + center.imag,
                    zadd=shifting, zscale=zoom, 
                    frames=frames, 
                    valmax=point_value_max, power=power, param=param)
        # print(julia.array)
        julia.iterate(steps, log_interval=1)
        julia.show(color_by, normalize_frame_depths=False)
        julia.image(folder=folder, colormap=colormap, animate=True, seconds=seconds)
    except Exception as e:
        print("Got exception:", e)
        if len(os.listdir(folder)) == 0:
            print("Deleting folder")
            shutil.rmtree(folder)
else:
    gif_julia(folder=folder, seconds=seconds)
end = datetime.now()
print(f'Done at {end}. Took {end - start}')