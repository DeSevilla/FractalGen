import numpy as np
import os
import shutil
import random
from fractal import Fractal, gif_folder, relative
from datetime import datetime
import matplotlib.pyplot as plt
from yaml import safe_load
import argparse

def configs(filename):
    return os.path.join('configs', filename)

def load_complex(s):
    if isinstance(s, complex) or isinstance(s, int) or isinstance(s, float):
        return s
    elif isinstance(s, str):
        return complex(''.join(s.split()).replace('i', 'j'))
    else:
        raise ValueError(f'Could not load complex number from {s} of type {type(s)}')

def randomize_config(filename='random.yaml'):
    with open(configs(filename), 'w') as file:
        run_type_options = ['julia', 'mandelbrot']
        file.write(f'run_type: {run_type_options[random.randint(0, 1)]}\n')
        file.write(f'xpixels: {random.randint(512, 2048)}\n')
        file.write(f'ypixels: {random.randint(512, 2048)}\n')
        file.write('frames: 1\n')
        colormaps = plt.colormaps()
        index = random.randint(0, len(colormaps) - 1)
        colormap = colormaps[index]
        file.write(f'colormap: {colormap}\n')
        color_by_options = ['iterations', 'diverged', 'undiverged', 'value', 'nested']
        file.write(f'color_by: {color_by_options[random.randint(0, len(color_by_options)-1)]}\n')
        file.write(f'height: {random.random() * 2.5 + .5}\n')
        center = f'{complex(random.random() * 3 - 1.5, random.random() * 3 - 1.5)}'
        file.write(f'center: {center}\n')
        file.write(f'point_value_max: {random.random() * 20}\n')
        file.write(f'steps: {random.randint(10, 200)}\n')
        file.write(f'power: {random.random() * 6}\n')
        param = f'{complex(random.random() * 3 - 1.5, random.random() * 3 - 1.5)}'
        file.write(f'param: {param}\n')
    return filename



def run_config(cfg: dict):
    start = datetime.now()
    run_type = cfg.get('run_type', 'julia')
    if run_type == 'reanimate':
        folder = cfg['folder']
        seconds = cfg.get('seconds', None)
        gif_folder(folder=folder, seconds=seconds)
        return
    pixels = cfg.get('pixels', 1024)
    xpixels = cfg.get('xpixels', pixels)
    ypixels = cfg.get('ypixels', pixels)
    aspect_ratio = xpixels / ypixels

    def check(coll: dict, has: list = None, no: list = None):
        if has is None:
            has = []
        if no is None:
            no = []
        return (
            all(map(lambda x: x in coll, has)) and 
            all(map(lambda x: x not in coll, no))
        )
    
    # def get(param, ii):
    #     if isinstance(param, np.ndarray):
    #         return param[ii]
    #     else:
    #         return param
    
    if check(cfg, has=['frames', 'fps'], no=['seconds']):
        frames = cfg.get('frames')
        seconds = cfg.get('fps') * frames
    elif check(cfg, has=['fps', 'seconds'], no=['frames']):
        seconds = cfg.get('seconds', 1)
        frames = cfg.get('fps') * seconds
    elif check(cfg, has=['frames', 'seconds'], no=['fps']):
        frames = cfg.get('frames', 1)
        seconds = cfg.get('seconds', min(1, frames / 24))
    elif check(cfg, has=['frames', 'seconds', 'fps']):
        raise ValueError(f'Config has frames, seconds, and fps. Leave one or more unspecified.')
    else:
        frames = cfg.get('frames', 1)
        if frames > 1:
            seconds = cfg.get('seconds', frames / 24)  # 24 fps default
        else:
            seconds = 0

    colormap_name = cfg.get('colormap', 'inferno')
    colormap = plt.get_cmap(colormap_name)
    color_by = cfg.get('color_by', 'iterations')
    normalize_frame_colors = cfg.get('normalize_frame_colors', False)
    height = cfg.get('height', 3)
    width = cfg.get('width', height * aspect_ratio)
    center = load_complex(cfg.get('center', 0))
    point_value_max = cfg.get('point_value_max', 2)
    if check(cfg, has=['steps_start', 'steps_end'], no=['steps']):
        steps_start = cfg['steps_start']
        steps_end = cfg['steps_end']
        steps_range = steps_end - steps_start
        # steps = np.linspace(steps_start, steps_end, frames)
        steps = np.asarray([int(steps_range * (i + 1) / frames) + steps_start for i in range(frames)])
        folder_steps = steps.max()
    elif check(cfg, no=['steps_start', 'steps_end']):
        steps = cfg.get('steps', 50)
        folder_steps = steps
    else:
        raise ValueError('Config must have either steps_start+steps_end or steps, not both.')

    if check(cfg, has=['zoom_start', 'zoom_end'], no=['zoom']):
        zoom_start = cfg['zoom_start']
        zoom_end = cfg['zoom_end']
        zscale = np.linspace(1 / zoom_start, 1 / zoom_end, frames)
    elif check(cfg, no=['zoom_start', 'zoom_end']):
        zoom = cfg.get('zoom', 1)
        zscale = np.full(frames, 1 / zoom)
    else:
        raise ValueError('Config must have either zoom_start+zoom_end or zoom, not both.')

    if check(cfg, has=['shift_start', 'shift_end'], no=['shift']):
        shift_start = load_complex(cfg['shift_start'])
        shift_end = load_complex(cfg['shift_end'])
        shift = np.linspace(shift_start, shift_end, frames)
    elif check(cfg, no=['shift_start', 'shift_end']):
        shift = load_complex(cfg.get('shift', 0))
    else:
        raise ValueError('Config must have either shift_start+shift_end or shift, not both.')

    shift = shift + (1 - zscale) * center  # this keeps the zoom centered, maybe?

    if check(cfg, has=['power_start', 'power_end'], no=['power']):
        power_start = cfg['power_start']
        power_end = cfg['power_end']
        power = np.linspace(power_start, power_end, frames)
    elif check(cfg, no=['power_start', 'power_end']):
        power = cfg.get('power', 2)
    else:
        raise ValueError('Config must have either power_start+power_end or power, not both.')

    radius_fixed = ['param_radius']
    degrees_fixed = ['param_degrees']
    radius_vary = ['param_radius_start', 'param_radius_end']
    degrees_vary = ['param_degrees_start', 'param_degrees_end']
    cart_fixed = ['param']
    cart_vary = ['param_start', 'param_end']
    polar = radius_vary + radius_fixed + degrees_fixed + degrees_vary
    cart = cart_fixed + cart_vary
    if check(cfg, has=radius_fixed + degrees_fixed, no=degrees_vary + radius_vary + cart):
        fixed_param = True
        param_radius = cfg['param_radius']
        param_degrees = cfg['param_degrees']
        param = param_radius * pow(np.e, complex(0, (param_degrees / 360) * 2 * np.pi))
    elif check(cfg, has=radius_fixed + degrees_vary, no=degrees_fixed + radius_vary + cart):
        fixed_param = False
        param_radius = cfg['param_radius']
        param_degrees_start = cfg['param_degrees_start']
        param_degrees_end = cfg['param_degrees_end']
        arcrange = param_degrees_end - param_degrees_start
        param = np.asarray([param_radius * pow(np.e, complex(0, ((n * arcrange / frames + param_degrees_start) / 360) * 2 * np.pi)) 
                            for n in range(frames)])
    elif check(cfg, has=radius_vary + degrees_fixed, no=degrees_vary + radius_fixed + cart):
        fixed_param = False
        param_radius_start = cfg['param_radius_start']
        param_radius_end = cfg['param_radius_end']
        param_degrees = cfg['param_degrees']
        angler = pow(np.e, complex(0, param_degrees / 360 * 2 * np.pi))
        param = np.linspace(param_radius_start * angler, param_radius_end * angler, frames)
    elif check(cfg, has=radius_vary + degrees_vary, no=degrees_fixed + radius_fixed + cart):
        fixed_param = False
        param_radius_start = cfg['param_radius_start']
        param_radius_end = cfg['param_radius_end']
        param_radius = np.linspace(param_radius_start, param_radius_end, frames)
        param_degrees_start = cfg['param_degrees_start']
        param_degrees_end = cfg['param_degrees_end']
        arcrange = param_degrees_end - param_degrees_start
        param = np.asarray([param_radius[n] * pow(np.e, complex(0, ((n * arcrange / frames + param_degrees_start) / 360) * 2 * np.pi)) 
                            for n in range(frames)])
    elif check(cfg, has=cart_vary, no=polar + cart_fixed):
        fixed_param = False
        param_start = load_complex(cfg.get('param_start'))
        param_end = load_complex(cfg.get('param_end'))
        param = np.linspace(param_start, param_end, frames)
    elif check(cfg, no=polar + cart_vary):  # doubles as default if no parameter is set
        fixed_param = True
        param = load_complex(cfg.get('param', -0.982+0.232j))
    else:
        raise ValueError("Incompatible specifications of complex parameter. For a fixed value use param (complex number) or param_radius+param_degrees (polar coordinates)"
                         "For a varying value use param_start+param_end (complex numbers), or a combination of param_radius_start+param_radius_end " 
                         "and/or param_degrees_start+param_degrees_end (polar coordinates).")
    folder = cfg.get('folder', 
                     relative('output', 
                              start.strftime('%Y%m%d%H%M%S') + '_unknown'))
    os.makedirs(folder, exist_ok=True)
    try:
        # print(power)
        fractal = Fractal(xpixels, ypixels, 
                    -width/2 + center.real, width/2 + center.real, -height/2 + center.imag, height/2 + center.imag,
                    zadd=shift, zscale=zscale, 
                    frames=frames)
        if run_type == 'julia':
            fractal.init_julia(power=power, param=param, valmax=point_value_max)
        elif run_type == 'mandelbrot':
            fractal.init_mandelbrot(power=power, valmax=point_value_max)
        else:
            raise ValueError(f'Run type must be either julia, mandelbrot, but was: {run_type}')
        fractal.iterate(steps, log_interval=10)
        fractal.show(color_by, normalize_frame_depths=normalize_frame_colors)
        fractal.image(folder=folder, colormap=colormap, animate=frames > 1, seconds=seconds)
    except Exception as e:
        if len(os.listdir(folder)) == 0:
            shutil.rmtree(folder)
        raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate either a Julia set or Mandelbrot variant.')
    parser.add_argument('YAML', nargs='?', default=None, help='path to a YAML config file, e.g. default.yaml')
    parser.add_argument('--random', '-r', action='store_true', help='generate a random config file')
    args = parser.parse_args()
    filename = args.YAML
    if args.random:
        if filename is None:
            filename = 'random.yaml'
        randomize_config(filename)
        print(f'Randomized config {filename}')
    while True:
        if filename is None:
            filename = input('Enter the name of a .yaml config file (or nothing to run default.yaml): ')
        if len(filename) == 0:
            filename = 'default.yaml'
        if os.path.exists(configs(filename)):
            break
        elif os.path.exists(configs(filename + '.yaml')):
            filename = filename + '.yaml'
            break
        else:
            print(f'File not found: {filename}')
            filename = None
    with open(configs(filename), 'r') as file:
        cfg = safe_load(file)
    if 'folder' not in cfg:
        folder_name = (datetime.now().strftime('%Y-%m-%d-%H%M%S') + ' ' + 
                       os.path.splitext(os.path.basename(filename))[0])
        cfg['folder'] = relative('output', folder_name)
    os.makedirs(cfg['folder'], exist_ok=True)
    shutil.copy2(configs(filename), cfg['folder'])
    start = datetime.now()
    run_config(cfg)
    end = datetime.now()
    print(f'Done in {end - start}')