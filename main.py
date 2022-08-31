import os
import shutil
from datetime import datetime
import numpy as np
from julia import Fractal, gif_folder, relative
from matplotlib import cm, colors
        

##############################################################
# Run type
##############################################################
run_type_options = [
    'julia',       # make a Julia set
    'mandelbrot',  # make a Mandelbrot-like set
    'reanimate'    # take an existing folder of .pngs and make it a gif
]
run_type = 'mandelbrot'
folder = None  # folder path. optional unless run_type is reanimate


##############################################################
# Display parameters
##############################################################
pixels = 1024  # pixel dimension of image
xpixels = pixels  # if you want to set x and y dimensions separately, you can change these variables
ypixels = pixels
aspect_ratio = xpixels / ypixels
frames = 1  # how many frames to generate
seconds = min(1, frames / 24)  # how many seconds the animation should last, if there is one
colormap = cm.inferno  # how to color the display. try cm.inferno, cm.viridis, cm.cool, cm.prism, and more!
# See https://matplotlib.org/stable/tutorials/colors/colormaps.html for more options and info
color_by_options = [
    'iterations', # color each point by how many iterations it lasted without diverging
    'diverged',   # how many iterations it took to diverge, or 0 if it didn't diverge
    'array',      # absolute value of each point (this will be the maximum value for any divergent point)
    'undiverged', # absolute value of each undivergent point, or 0 for any divergent point
    'nested'      # how many iterations it took to diverge, or absolute value if it didn't diverge
]
color_by = 'diverged'
normalize_frame_colors = False  # try to maintain consistent colors for specific data values between frames
# If the number of steps varies between frames and you are displaying iterations, 
# having this as True will show undiverged points differently between different frames.

##############################################################
# Fixed simulation parameters
##############################################################
# size = 3
height = 3  # height of the viewing window in the complex plane
width = height * aspect_ratio
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
    steps_end = 130

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
    shift_end = complex(2, 2)

# the step equation for any point is x^p + c. this sets p
power = None  # placeholder
fixed_power = True
if fixed_power:
    power = 2
else:
    power_start = 1
    power_end = 5

# the step equation for any point is x^p + c. this sets c
param = None  # placeholder
fixed_param = True
param_radius = 0.8  # this applies to both fixed and variable parameters
if fixed_param:
    # you can also just set param equal to any complex number here
    param_degrees = 169
    # param = complex(-0.3632, 0.7128)
else:
    # default setup traces a circle in the complex plane, this sets the range
    param_degrees_center = 135
    param_degrees_range = 40
    param_degrees_start = param_degrees_center - param_degrees_range / 2
    param_degrees_end = param_degrees_center + param_degrees_range / 2

start = datetime.now()
if run_type == 'reanimate':
    gif_folder(folder=folder, seconds=seconds)
else:
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
        # steps = np.linspace(steps_start, steps_end, frames)
        steps = np.asarray([int(steps_range * (i + 1) / frames) + steps_start for i in range(frames)])
        folder_steps = steps.max()

    if zscale is None:
        if fixed_zoom:
            zscale = np.full(frames, 1 / zoom)
        else:
            zscale = np.linspace(1 / zoom_start, 1 / zoom_end, frames)

    if shifting is None:
        if not fixed_shift:
            shifting = np.linspace(shift_start, shift_end, frames)
        else:
            print('undefined shift?')
    shifting = shifting + (1 - zscale) * center  # this keeps the zoom centered

    if power is None:
        if not fixed_param:
            power = np.linspace(power_start, power_end, frames)
        else:
            print('Power undefined???')

    if fixed_param:
        if param is None:
            param = param_radius * pow(np.e, complex(0, (param_degrees / 360) * 2 * np.pi))
        folder_param = f'{np.abs(param):.3f}r{np.angle(param, deg=True):.02f}d'
    else:
        arcrange = param_degrees_end - param_degrees_start
        param = np.asarray([param_radius * pow(np.e, complex(0, ((n * arcrange / frames + param_degrees_start) / 360) * 2 * np.pi)) 
                            for n in range(frames)])
        folder_param = f'{param_radius:.3f}r{param_degrees_start:.02f}-{param_degrees_end:.02f}d'
    if folder is None:
        folder = relative('output', start.strftime('%Y%m%d%H%M%S') + 
                         f' {xpixels}x{ypixels}px {height:.02f}x{width:.02f}w {frames}f {folder_steps}s {folder_param}p')
    os.makedirs(folder)
    try:
        julia = Fractal(xpixels, ypixels, 
                    -width/2 + center.real, width/2 + center.real, -height/2 + center.imag, height/2 + center.imag,
                    zadd=shifting, zscale=zscale, 
                    frames=frames)
        if run_type == 'julia':
            julia.init_julia(power=power, param=param, valmax=point_value_max)
        elif run_type == 'mandelbrot':
            julia.init_mandelbrot(power=power, valmax=point_value_max)
        else:
            raise ValueError(f'Run type must be either julia or mandelbrot, but was: {run_type}')
        # print(julia.array)
        julia.iterate(steps, log_interval=1)
        julia.show(color_by, normalize_frame_depths=normalize_frame_colors)
        julia.image(folder=folder, colormap=colormap, animate=True, seconds=seconds)
    except Exception as e:
        print("Got exception:", e)
        if len(os.listdir(folder)) == 0:
            print("Deleting folder")
            shutil.rmtree(folder)
        raise e
end = datetime.now()
print(f'Done at {end}. Took {end - start}')