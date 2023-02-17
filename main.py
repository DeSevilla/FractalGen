import numpy as np
import os
import shutil
import random
from fractal import Fractal, gif_folder, relative
from datetime import datetime
import matplotlib.pyplot as plt
from yaml import safe_load
import argparse
import regex

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
    frames = cfg.get('frames', 1)
    seconds = cfg.get('seconds', min(1, frames / 24))
    colormap_name = cfg.get('colormap', 'inferno')
    colormap = plt.get_cmap(colormap_name)
    color_by = cfg.get('color_by', 'iterations')
    normalize_frame_colors = cfg.get('normalize_frame_colors', False)
    height = cfg.get('height', 3)
    width = cfg.get('width', height * aspect_ratio)
    center = load_complex(cfg.get('center', 0))
    point_value_max = cfg.get('point_value_max', 2)
    if 'steps_start' in cfg and 'steps_end' in cfg:
        steps_start = cfg['steps_start']
        steps_end = cfg['steps_end']
        steps_range = steps_end - steps_start
        # steps = np.linspace(steps_start, steps_end, frames)
        steps = np.asarray([int(steps_range * (i + 1) / frames) + steps_start for i in range(frames)])
        folder_steps = steps.max()
    else:
        steps = cfg.get('steps', 50)
        folder_steps = steps

    if 'zoom_start' in cfg and 'zoom_end' in cfg:
        zoom_start = cfg['zoom_start']
        zoom_end = cfg['zoom_end']
        zscale = np.linspace(1 / zoom_start, 1 / zoom_end, frames)
    else:
        zoom = cfg.get('zoom', 1)
        zscale = np.full(frames, 1 / zoom)

    if 'shift_start' in cfg and 'shift_end':
        shift_start = load_complex(cfg['shift_start'])
        shift_end = load_complex(cfg['shift_end'])
        shift = np.linspace(shift_start, shift_end, frames)
    else:
        shift = load_complex(cfg.get('shift', 0))
    shift = shift + (1 - zscale) * center  # this keeps the zoom centered, maybe?

    if 'power_start' in cfg and 'power_end' in cfg:
        power_start = cfg['power_start']
        power_end = cfg['power_end']
        power = np.linspace(power_start, power_end, frames)
    else:
        power = cfg.get('power', 2)

    if 'param_degrees_start' in cfg and 'param_degrees_end' and 'param_radius' in cfg:
        fixed_param = False
        param_radius = cfg['param_radius']
        param_degrees_start = cfg['param_degrees_start']
        param_degrees_end = cfg['param_degrees_end']
        arcrange = param_degrees_end - param_degrees_start
        param = np.asarray([param_radius * pow(np.e, complex(0, ((n * arcrange / frames + param_degrees_start) / 360) * 2 * np.pi)) 
                            for n in range(frames)])
    elif 'param_radius' in cfg and 'param_degrees' in cfg:
        fixed_param = True
        param_radius = cfg['param_radius']
        param_degrees = cfg['param_degrees']
        param = param_radius * pow(np.e, complex(0, (param_degrees / 360) * 2 * np.pi))
    else:
        fixed_param = True
        param = load_complex(cfg.get('param', -0.982+0.232j))
    if fixed_param:
        folder_param = f'{np.abs(param):.3f}r{np.angle(param, deg=True):.02f}d'
    else:
        folder_param = f'{param_radius:.3f}r{param_degrees_start:.02f}-{param_degrees_end:.02f}d'

    folder = cfg.get('folder', 
                     relative('output', 
                              start.strftime('%Y%m%d%H%M%S') + 
                              f' {xpixels}x{ypixels}px {height:.02f}x{width:.02f}w {frames}f {folder_steps}s {folder_param}p'))
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
            raise ValueError(f'Run type must be either julia or mandelbrot, but was: {run_type}')
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