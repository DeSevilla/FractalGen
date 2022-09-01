import numpy as np
import os
import shutil
from julia import Fractal, gif_folder, relative
from datetime import datetime
import matplotlib.pyplot as plt
from yaml import safe_load, load, Loader


def load_cfg(cfg: dict):
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
    seconds = cfg.get('seconds', min(1, frames / 24)  )
    colormap_name = cfg.get('colormap', 'inferno')
    colormap = plt.get_cmap(colormap_name)
    color_by = cfg.get('color_by', 'iterations')
    normalize_frame_colors = cfg.get('normalize_frame_colors', False)
    height = cfg.get('height', 3)
    width = cfg.get('width', height * aspect_ratio)
    center = cfg.get('center', 0)
    point_value_max = cfg.get('point_value_max', 10)
    if 'steps' in cfg:
        steps = cfg['steps']
        folder_steps = steps
    else:
        steps_start = cfg.get('steps_start', 10)
        steps_end = cfg.get('steps_end', 130)
        steps_range = steps_end - steps_start
        # steps = np.linspace(steps_start, steps_end, frames)
        steps = np.asarray([int(steps_range * (i + 1) / frames) + steps_start for i in range(frames)])
        folder_steps = steps.max()

    if 'zoom' in cfg:
        zoom = cfg['zoom']
        zscale = np.full(frames, 1 / zoom)
    else:
        zoom_start = cfg.get('zoom_start', 1)
        zoom_end = cfg.get('zoom_end', 1)
        zscale = np.linspace(1 / zoom_start, 1 / zoom_end, frames)

    if 'shift' in cfg:
        shift = cfg['shift']
    else:
        shift_start = cfg.get('shift_start', 1)
        shift_end = cfg.get('shift_end', 10)
        shift = np.linspace(shift_start, shift_end, frames)
    shift = shift + (1 - zscale) * center  # this keeps the zoom centered


    if 'power' in cfg:
        power = cfg['power']
    else:
        power_start = cfg.get('power_start', 1)
        power_end = cfg.get('power_end', 10)
        power = np.linspace(power_start, power_end, frames)
    # the step equation for any point is x^p + c. this sets c

    if 'param' in cfg:
        fixed_param = True
        param = cfg['param']
    elif 'param_radius' in cfg and 'param_degrees' in cfg:
        fixed_param = True
        param_radius = cfg.get('param_radius', 0.8)
        param_degrees = cfg.get('param_degrees', 169)
        param = param_radius * pow(np.e, complex(0, (param_degrees / 360) * 2 * np.pi))
    else:
        fixed_param = False
        param_radius = cfg.get('param_radius', 0.8)
        if 'param_degrees_center' in cfg and 'param_degrees_range' in cfg:
            param_degrees_center = cfg.get('param_degrees_center', 135)
            param_degrees_range = cfg.get('param_degrees_range', 40)
            param_degrees_start = param_degrees_center - param_degrees_range / 2
            param_degrees_end = param_degrees_center + param_degrees_range / 2
        else:
            param_degrees_start = cfg.get('param_degrees_start', 120)
            param_degrees_end = cfg.get('param_degrees_end', 240)
        arcrange = param_degrees_end - param_degrees_start
        param = np.asarray([param_radius * pow(np.e, complex(0, ((n * arcrange / frames + param_degrees_start) / 360) * 2 * np.pi)) 
                            for n in range(frames)])
    if fixed_param:
        folder_param = f'{np.abs(param):.3f}r{np.angle(param, deg=True):.02f}d'
    else:
        folder_param = f'{param_radius:.3f}r{param_degrees_start:.02f}-{param_degrees_end:.02f}d'
    folder = cfg.get('folder', 
                     relative('output', 
                              start.strftime('%Y%m%d%H%M%S') + 
                              f' {xpixels}x{ypixels}px {height:.02f}x{width:.02f}w {frames}f {folder_steps}s {folder_param}p'))
    os.makedirs(folder)
    try:
        julia = Fractal(xpixels, ypixels, 
                    -width/2 + center.real, width/2 + center.real, -height/2 + center.imag, height/2 + center.imag,
                    zadd=shift, zscale=zscale, 
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

if __name__ == '__main__':
    with open('variable.yaml', 'r') as file:
        cfg = load(file, Loader=Loader)
    load_cfg(cfg)