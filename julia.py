from datetime import datetime
import numpy as np
from PIL import Image
from matplotlib import cm, colors
import os

from regex import W

def relative(*args):
    return os.path.join(os.path.dirname(__file__), *args)

class Julia:
    def __init__(self, xpixels, ypixels, xmin=-1, xmax=1, ymin=-1, ymax=1, zadd=None, zscale=None, frames=1,
                 power=2, param=complex(-0.982, 0.21), valmax=2):
        self.frames = frames
        self.xpixels = xpixels
        self.ypixels = ypixels
        x = np.linspace(xmin, xmax, xpixels)
        y = np.linspace(ymin, ymax, ypixels)
        if zscale is None:
            zscale = np.ones(self.frames)
        zs, xs, ys = np.meshgrid(zscale, x, y, sparse=True, indexing='ij')
        self.array = zs * (xs + 1j * ys)
        if zadd is not None:
            self.array += zadd[:, np.newaxis, np.newaxis]
        self.array = self.array.astype(np.complex64, casting='same_kind', copy=False)
        self.iterations = np.zeros(self.array.shape, dtype=np.uint16)
        self.to_show = None
        self.total_steps = 0
        self.arraypower = isinstance(power, np.ndarray)
        self.arrayparam = isinstance(param, np.ndarray)
        if self.arraypower:
            self.power = np.broadcast_to(power[:, np.newaxis, np.newaxis], self.array.shape)
        else:
            self.power = power
        if self.arrayparam:
            self.param = np.broadcast_to(param[:, np.newaxis, np.newaxis], self.array.shape)
        else:
            self.param = param
        if np.abs(param).max() > 2:
            print('Warning: parameter will produce bad values')
        self.valmax = valmax

        
    def iterate(self, steps=1, log_interval=-1):
        if isinstance(steps, np.ndarray):
            arraysteps = True
            n = steps.max()
            steps = np.broadcast_to(steps[:, np.newaxis, np.newaxis], self.array.shape)
        else:
            arraysteps = False
            n = steps
        usepow = self.power
        usepar = self.param
        for k in range(n):
            if log_interval > 0 and k % log_interval == 0:
                print(f'{k}/{n}') 
            absarray = np.abs(self.array)
            to_update = absarray < self.valmax
            if arraysteps:
                to_update = np.logical_and(to_update, steps > k)
            if self.arraypower:
                usepow = self.power[to_update]
            if self.arrayparam:
                usepar = self.param[to_update]
            self.array[to_update] **= usepow
            self.array[to_update] += usepar
            self.iterations[to_update] += 1
            self.total_steps += 1
            self.to_show = self.iterations

    def iterate_wrapping(self, n=1, log_interval=-1):
        for k in range(n):
            if log_interval > 0 and k % log_interval == 0: 
                print(f'{k}/{n}') 
            self.array **= self.power
            self.array += self.param
            absarray = np.abs(self.array)
            divergent = absarray > self.valmax
            self.array[divergent] = 0
            self.iterations[divergent] = k + 1
            self.total_steps += 1
        self.iterations[self.iterations == 0] = self.total_steps
        self.to_show = self.array

    def show(self, show_type='iterations', normalize_frame_depths=True):
        if normalize_frame_depths:
            self.iterations[:, 0, 0] = 0
            self.iterations[:, 0, 1] = self.total_steps
            self.array[:, 0, 0] = 0
            self.array[:, 0, 1] = np.abs(self.array).max()
        if show_type == 'iterations':
            self.to_show = self.iterations
        elif show_type == 'array':
            self.to_show = self.array
        elif show_type == 'undiverged':
            undiverged = self.iterations == self.total_steps
            absvals = np.abs(self.array[undiverged]) / np.abs(self.array[undiverged].max()) * self.iterations.max()
            self.to_show = np.zeros(self.array.shape)
            self.to_show[undiverged] = absvals
        elif show_type == 'nested':
            self.to_show = self.iterations
            undiverged = self.iterations == self.total_steps
            absvals = np.abs(self.array[undiverged]) / np.abs(self.array[undiverged].max()) * self.iterations.max()
            print(absvals.min(), absvals.max())
            self.to_show[undiverged] = absvals
        elif show_type == 'diverged':
            self.to_show = self.iterations
            self.to_show[self.iterations == self.total_steps] = 0
        elif show_type == 'wtf':
            self.to_show = self.iterations
            self.to_show[self.iterations > self.total_steps] = 0
        else:
            print('Invalid display type')

    def image(self, folder=None, grayscale=False, colormap=None, animate=True, seconds=0):
        if colormap is None:
            colormap = cm.viridis
        if self.to_show is None:
            print('No image to show defined yet')
            return
        if folder is None:
            folder = 'output'
        images = []
        for k in range(self.to_show.shape[0]):
            abs_array = np.abs(self.to_show[k])
            if abs_array.max() > 0:
                scaled = abs_array / abs_array.max()
            else:
                scaled = abs_array
            scaled = np.flip(scaled, axis=0)
            if grayscale:
                im = Image.fromarray(np.uint8(scaled * 255), 'L')
            else:
                im = Image.fromarray(np.uint8(colormap(scaled) * 255), 'RGBA')
            if self.arrayparam:
                angle = np.angle(self.param[k][0][0], deg=True)
            else:
                angle = np.angle(self.param, deg=True)
            angle_str = f'{angle % 360:.02f}'.replace('.', '_')
            filename = f'julia{k:04}_{angle_str}.png'
            im.save(relative('output', folder, filename))
            print(f'saving at {filename}')
            if animate:
                images.append(im)
        if animate:
            print(len(images))
            if len(images) > 1:
                save_gif(images, relative(folder, 'julia_animated.gif'), seconds=seconds)
            else:
                print('Cannot animate as there is only one frame')

def save_gif(images, path, seconds=-1):
    print('Saving at', path)
    for i in range(len(images)):
        images[i] = images[i].convert('P', palette=Image.ADAPTIVE)
    if seconds > 0:
        duration = seconds * 1000 / len(images)
    else:
        duration = 50
    images[0].save(path, save_all=True, append_images=images[1:], duration=duration, loop=0, disposal=2)

def gif_julia(folder, seconds=0):
    images = []
    pngs = sorted(filter(lambda fn: os.path.splitext(fn)[1] == '.png', os.listdir(folder)))
    for fn in pngs:
        im = Image.open(relative('output', folder, fn))
        images.append(im.convert('P', palette=Image.ADAPTIVE)) 
    save_gif(images, relative('output', folder, f'julia_animated.gif'), seconds=seconds)
       

if __name__ == '__main__':
    frames = 12
    start = datetime.now()
    folder = None  # relative('output', '20220827163008 2048px 60f 3w 200s 169a30r')
    if folder is None:
        # def _colormap_red(x): return 0.75 * np.sin((x * 2 + .25) * np.pi) + 0.67
        # def _colormap_green(x): return .75 * np.sin((x * 2 - 0.25) * np.pi) + 0.33
        # def _colormap_blue(x): return -1.1 * np.sin((x * 2) * np.pi)
        # colormap_spec = {'red': _colormap_red, 'green': _colormap_green, 'blue': _colormap_blue}
        # colormap = colors.LinearSegmentedColormap('custom', colormap_spec)
        colormap = cm.inferno
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
                        valmax=10, power=power, param=param,
                        frames=frames)
            # print(julia.array)
            julia.iterate(steps, log_interval=1)
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
