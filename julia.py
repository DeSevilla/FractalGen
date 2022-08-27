from datetime import datetime
import math
import numpy as np
from PIL import Image
from matplotlib import cm
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
        xs, ys = np.meshgrid(x, y, sparse=True)
        complex_plane = xs + 1j * ys
        print('Built first plane')
        self.array = np.repeat(complex_plane[np.newaxis, :, :], self.frames, axis=0)
        self.array = self.array.astype(np.complex64, casting='same_kind', copy=False)
        print('Built remaining planes')
        self.iterations = np.zeros(self.array.shape, dtype=np.uint16)
        self.to_show = None
        self.steps = None
        
    def iterate(self, n=1, log_interval=-1, valmax=2, param=None):
        if param is None:
            param = np.full((self.array.shape[0],), complex(-0.835, -0.231))
        elif np.abs(param).max() > 2:
            print('Warning: parameter outside Mandelbrot set and will produce bad values')
        self.steps = n
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
        self.steps = n
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

    def image(self, folder=None, grayscale=False, colormap=None):
        if colormap is None:
            colormap = cm.viridis
        if self.to_show is None:
            print('No image to show defined yet')
            return
        if folder is None:
            folder = 'output'
        filename = relative(folder, 'julia_animated.gif')
        images = []
        for k in range(self.to_show.shape[0]):
            abs_array = np.abs(self.to_show[k])
            if abs_array.max() > 0:
                scaled = abs_array / abs_array.max()
            else:
                scaled = abs_array
            scaled = np.transpose(scaled)
            if grayscale:
                im = Image.fromarray(np.uint8(scaled * 255), 'L')
            else:
                im = Image.fromarray(np.uint8(colormap(scaled) * 255), 'RGBA')
            angle = f'{np.angle(param[k], deg=True):.02f}'.replace('.', '_')
            filename = f'julia{k}_{angle}.png'
            im.save(relative('output', folder, filename))
            print(f'saving at {filename}')
            images.append(im.convert('P', palette=Image.Palette.ADAPTIVE))
        if self.to_show.shape[0] > 1:
            save_gif(images, filename)

def save_gif(images, path):
    images[0].save(path, save_all=True, append_images=images[1:], duration=50, loop=0, disposal=2)

def gif_julia(folder):
    images = []
    pngs = sorted(filter(lambda fn: os.path.splitext(fn)[1] == '.png', os.listdir(folder)))
    for fn in pngs:
        im = Image.open(relative('output', folder, fn))
        images.append(im.convert('P', palette=Image.Palette.ADAPTIVE))
    save_gif(images, relative('output', folder, f'julia_animated.gif'))


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
    frames = 1
    start = datetime.now()
    size = 3
    pixels = 2048
    steps = 60
    folder = None
    if folder is None:
        folder = relative('output', start.strftime('%Y-%m-%d %H.%M.%S') + f' f{frames} p{pixels} w{size} s{steps}')
        arccenter = 120
        os.makedirs(folder)
        arcrange = 30
        arcmin = arccenter - arcrange / 2
        # param = np.full((frames,), complex(.5, -.5))
        param = np.asarray([0.8 * pow(math.e, complex(0, ((n * arcrange / frames + arcmin) / 360) * math.tau)) for n in range(frames)])
        # julia = Julia(pixels, pixels, -size/2, size/2, -size/2, size/2, frames=frames)
        julia = Julia(pixels, pixels, -0.2, 0.1, 0.35, 0.65, frames=frames)
        julia.iterate(steps, log_interval=1, valmax=10, param=param)
        julia.show('diverged')
        julia.image(folder=folder)
    else:
        gif_julia(frames, folder=folder)
    end = datetime.now()
    print(f'Done at {end}. Took {end - start}')
