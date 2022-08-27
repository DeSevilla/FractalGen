from datetime import datetime
import numpy as np
from PIL import Image
from matplotlib import cm, colors
import os

from regex import W

def relative(*args):
    return os.path.join(os.path.dirname(__file__), *args)

class Julia:
    def __init__(self, xpixels, ypixels, xmin=-1, xmax=1, ymin=-1, ymax=1, frames=1):
        self.frames = frames
        self.xpixels = xpixels
        self.ypixels = ypixels
        x = np.linspace(xmin, xmax, xpixels)
        y = np.linspace(ymin, ymax, ypixels)
        z = np.ones(self.frames)
        zs, xs, ys = np.meshgrid(z, x, y, sparse=True, indexing='ij')
        self.array = zs * (xs + 1j * ys)
        self.array = self.array.astype(np.complex64, casting='same_kind', copy=False)
        self.iterations = np.zeros(self.array.shape, dtype=np.uint16)
        self.to_show = None
        self.steps = 0
        
    def iterate(self, n=1, log_interval=-1, valmax=2, param=None):
        if param is None:
            param = np.full((self.array.shape[0],), complex(-0.835, -0.231))
        elif np.abs(param).max() > 2:
            print('Warning: parameter outside Mandelbrot set and will produce bad values')
        self.steps += n
        for k in range(self.steps):
            if log_interval > 0 and k % log_interval == 0:
                print(f'{k}/{n}') 
            absarray = np.abs(self.array)
            undiverged = absarray < valmax
            self.array[undiverged] *= self.array[undiverged]
            self.array += param[:, np.newaxis, np.newaxis]
            self.iterations[undiverged] += 1
        undiverged = np.abs(self.array) < valmax
        self.to_show = self.iterations

    def iterate_wrapping(self, n=1, log_interval=-1, valmax=1, param=None):
        if param is None:
            param = np.full((self.array.shape[0],), complex(-0.835, -0.231))
        self.steps += n
        for k in range(self.steps):
            if log_interval > 0 and k % log_interval == 0: 
                print(f'{k}/{n}') 
            self.array = self.array ** 2
            self.array += param[:, np.newaxis, np.newaxis]
            absarray = np.abs(self.array)
            divergent = absarray > valmax
            self.array[divergent] = 0
            self.iterations[divergent] = k + 1
        self.iterations[self.iterations == 0] = self.steps
        self.to_show = self.array

    def show(self, show_type='iter'):
        if show_type == 'iterations':
            self.to_show = self.iterations
        elif show_type == 'array':
            self.to_show = self.array
        elif show_type == 'undiverged':
            undiverged = self.iterations == self.steps
            absvals = np.abs(self.array[undiverged]) / np.abs(self.array[undiverged].max()) * self.iterations.max()
            self.to_show = np.zeros(self.array.shape)
            self.to_show[undiverged] = absvals
        elif show_type == 'nested':
            self.to_show = self.iterations
            undiverged = self.iterations == self.steps
            absvals = np.abs(self.array[undiverged]) / np.abs(self.array[undiverged].max()) * self.iterations.max()
            print(absvals.min(), absvals.max())
            self.to_show[undiverged] = absvals
        elif show_type == 'diverged':
            self.to_show = self.iterations
            self.to_show[self.iterations == self.steps] = 0
        elif show_type == 'wtf':
            self.to_show = self.iterations
            self.to_show[self.iterations > self.steps] = 0

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
            if animate:
                scaled[0][0] = 0
                scaled[0][1] = 1
            if grayscale:
                im = Image.fromarray(np.uint8(scaled * 255), 'L')
            else:
                im = Image.fromarray(np.uint8(colormap(scaled) * 255), 'RGBA')
            angle = f'{np.angle(param[k], deg=True) % 360:.02f}'.replace('.', '_')
            filename = f'julia{k:04}_{angle}.png'
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

def save_gif(images, path, seconds=0):
    print('Saving at', path)
    # palette = None
    for i in range(len(images)):
        # if palette is None:
        #     im = images[i].convert('P', palette=Image.Palette.ADAPTIVE)
        #     palette = im.getpalette()
        #     images[i] = im
        # else:
        images[i] = images[i].convert('P', palette=Image.Palette.ADAPTIVE)
    if seconds == 0:
        duration = 50
    else:
        duration = seconds * 1000 / len(images)
    images[0].save(path, save_all=True, append_images=images[1:], duration=duration, loop=0, disposal=2)

def gif_julia(folder, seconds=0):
    images = []
    pngs = sorted(filter(lambda fn: os.path.splitext(fn)[1] == '.png', os.listdir(folder)))
    for fn in pngs:
        im = Image.open(relative('output', folder, fn))
        images.append(im.convert('P', palette=Image.Palette.ADAPTIVE)) 
    save_gif(images, relative('output', folder, f'julia_animated.gif'), seconds=seconds)


def test_iterate(julia, n=1, valmax=200, param=None):
    if param is None:
        param = np.full((julia.array.shape[0],), complex(-0.835, -0.231))
    array2 = np.copy(julia.array)
    iterations2 = np.copy(julia.iterations)
    julia.iterate(n=n, valmax=valmax, param=param) 
    shape = array2.shape
    julia.steps = n
    for step in range(julia.steps):
        for i in range(shape[0]):
            for j in range(shape[1]):
                if j % 100 == 0:
                    print(f'on row {j} of {shape[1]}')
                for k in range(shape[2]):
                    if abs(array2[i][j][k]) < valmax:
                        array2[i][j][k] = array2[i][j][k] * array2[i][j][k]
                        iterations2[i][j][k] += 1
                    array2[i][j][k] += param[i]
    print(julia.iterations.max(), julia.iterations.min(), iterations2.max(), iterations2.min())
    print(julia.array.max(), julia.array.min(), array2.max(), array2.min())
    print(np.array_equal(julia.iterations, iterations2))
    print(np.array_equal(julia.array, array2))
    julia.to_show = julia.array - array2

        

if __name__ == '__main__':
    frames = 30
    start = datetime.now()
    pixels = 1500
    steps = 60
    folder = None # relative('output', '2022-08-27 15.01.03 1500px 30s 30f')
    if folder is None:
        # def _colormap_red(x): return 0.75 * np.sin((x * 5 + .25) * np.pi) + 0.67
        # def _colormap_green(x): return .75 * np.sin((x * 5 - 0.25) * np.pi) + 0.33
        # def _colormap_blue(x): return -1.1 * np.sin((x * 5) * np.pi)
        # colormap_spec = {'red': _colormap_red, 'green': _colormap_green, 'blue': _colormap_blue}
        # colormap = colors.LinearSegmentedColormap('custom', colormap_spec)
        colormap = cm.inferno
        # matplotlib predefined colormap - cm.viridis, cm.ocean, cm.plasma, cm.gist_earth, etc.
        # window parameters
        size = 3
        center = (0, 0)

        # complex parameter location (range is broken up into frames)
        arccenter = 169
        arcrange = 30
        arcmin = arccenter - arcrange / 2

        folder = relative('output', start.strftime('%Y%m%d%H%M%S') + f' {pixels}px {frames}f {size}w {steps}s {arccenter}a{arcrange}r')
        os.makedirs(folder)
        # param = np.full((frames,), complex(.5, -.5))
        param = np.asarray([0.8 * pow(np.e, complex(0, ((n * arcrange / frames + arcmin) / 360) * 2 * np.pi)) for n in range(frames)])
        julia = Julia(pixels, pixels, -size/2 + center[0], size/2 + center[0], -size/2 + center[1], size/2 + center[1], frames=frames)
        julia.iterate(steps, log_interval=1, valmax=10, param=param)
        julia.show('diverged')
        julia.image(folder=folder, colormap=colormap, animate=False, seconds=frames / 15)
    else:
        gif_julia(folder=folder, seconds=frames / 24)
    end = datetime.now()
    print(f'Done at {end}. Took {end - start}')
