import os
from datetime import datetime
import numpy as np
from julia import Julia, gif_julia, relative
from matplotlib import cm, colors
        

if __name__ == '__main__':
    frames = 1
    start = datetime.now()
    folder = None  # relative('output', '20220827163008 2048px 60f 3w 200s 169a30r')
    if folder is None:
        # def _colormap_red(x): return 0.75 * np.sin((x * 2 + .25) * np.pi) + 0.67
        # def _colormap_green(x): return .75 * np.sin((x * 2 - 0.25) * np.pi) + 0.33
        # def _colormap_blue(x): return -1.1 * np.sin((x * 2) * np.pi)
        def _colormap_red(x): return x
        def _colormap_green(x): return 0
        def _colormap_blue(x): return 0
        colormap_spec = {'red': _colormap_red, 'green': _colormap_green, 'blue': _colormap_blue}
        colormap = colors.LinearSegmentedColormap('custom', colormap_spec)
        # colormap = cm.inferno
        # matplotlib predefined colormaps are useful here - cm.viridis, cm.ocean, cm.plasma, cm.gist_earth, etc.
        # my favorite is cm.inferno
        # try cm.prism some time, it's ugly as sin
        # the custom colormap is a prism variant (doesn't move as fast so it's somewhat less ugly) 

        # window parameters
        pixels = 1024
        size = 3
        center = 0
        # center = complex(0.195, 0.245)
        zoom = None  # vector of how much to zoom in the window relative to start, per frame; smaller shrinks the window
        shifting = None  # vector of how much to move the window relative to start per frame
        # zoom = np.full(frames, 1 - 75/120)
        # zoom = np.asarray([1-i/frames for i in range(frames)])  
        # shifting = (1 - zoom) * center  # this keeps the zoom centered

        # general simulation parameters
        steps = 100
        power = 2 # np.asarray([3 + i * 3 / frames for i in range(frames)])

        # complex parameter location (range is broken up into frames)
        # arccenter = 169.81
        arccenter = 169.81
        arcrange = 30
        arcmin = arccenter - arcrange / 2
        param = np.asarray([0.8 * pow(np.e, complex(0, ((n * arcrange / frames + arcmin) / 360) * 2 * np.pi)) for n in range(frames)])
        # param = 0.8 * pow(np.e, complex(0, arcmin / 360) * 2 * np.pi)

        folder = relative('output', start.strftime('%Y%m%d%H%M%S') + 
                         f' {pixels}px {frames}f {size}w {steps}s {arccenter}a{arcrange}r')
        os.makedirs(folder)
        try:
            julia = Julia(pixels, pixels, 
                        -size/2 + center.real, size/2 + center.real, -size/2 + center.imag, size/2 + center.imag,
                        zadd=shifting, zscale=zoom, 
                        frames=frames)
            # print(julia.array)
            julia.iterate(steps, log_interval=1, valmax=10, power=power, param=param)
            julia.show('iterations')
            julia.image(folder=folder, colormap=colormap, animate=True, seconds=min(1, frames / 24))
        except Exception as e:
            print("Got exception:", e)
            if len(os.listdir(folder)) == 0:
                print("Deleting folder")
                os.remove(folder)
    else:
        gif_julia(folder=folder, seconds=frames / 15)
    end = datetime.now()
    print(f'Done at {end}. Took {end - start}')