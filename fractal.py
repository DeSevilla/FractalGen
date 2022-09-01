import numpy as np
from PIL import Image
from matplotlib import cm
import os

def relative(*args):
    return os.path.join(os.path.dirname(__file__), *args)

class Fractal:
    def __init__(self, xpixels, ypixels, xmin=-1, xmax=1, ymin=-1, ymax=1, zadd=None, zscale=None, frames=1):
        self.frames = frames
        self.xpixels = xpixels
        self.ypixels = ypixels
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        if zscale is None:
            self.zscale = np.ones(self.frames)
        else:
            self.zscale = zscale
        self.zadd = zadd
        self.zscale = zscale
        self.total_steps = 0
        self.array = None
        self.iterations = None
        self.to_show = None
        self.power = None
        self.param = None
        self.arraypower = None
        self.arrayparam = None
        self.valmax = None

    def init_julia(self, power=2, param=complex(-0.982, 0.21), valmax=2):
        x = np.linspace(self.xmin, self.xmax, self.xpixels)
        y = np.linspace(self.ymin, self.ymax, self.ypixels)
        zs, xs, ys = np.meshgrid(self.zscale, x, y, sparse=True, indexing='ij')
        self.array = zs * (xs + 1j * ys)
        if self.zadd is not None:
            self.array += self.zadd[:, np.newaxis, np.newaxis]
        self.array = self.array.astype(np.complex64, casting='same_kind', copy=False)
        self.iterations = np.zeros(self.array.shape, dtype=np.uint16)
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
        self.valmax = valmax

    def init_mandelbrot(self, power=2, valmax=2):
        self.array = np.zeros((self.frames, self.xpixels, self.ypixels), dtype=np.complex64)
        self.iterations = np.zeros((self.frames, self.xpixels, self.ypixels), dtype=np.uint16)
        self.power = power
        self.arraypower = isinstance(power, np.ndarray)
        if self.arraypower:
            self.power = np.broadcast_to(power[:, np.newaxis, np.newaxis], self.array.shape)
        else:
            self.power = power
        x = np.linspace(self.xmin, self.xmax, self.xpixels)
        y = np.linspace(self.ymin, self.ymax, self.ypixels)
        zs, xs, ys = np.meshgrid(self.zscale, x, y, indexing='ij')
        self.param = zs * (xs + 1j * ys)
        self.param = self.param.astype(np.complex64, casting='same_kind', copy=False)
        self.arrayparam = True
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
        print('Saving images...')
        for k in range(self.to_show.shape[0]):
            abs_array = np.abs(self.to_show[k])
            if abs_array.max() > 0:
                scaled = abs_array / abs_array.max()
            else:
                scaled = abs_array
            scaled = np.transpose(np.flip(scaled, axis=1))
            if grayscale:
                im = Image.fromarray(np.uint8(scaled * 255), 'L')
            else:
                im = Image.fromarray(np.uint8(colormap(scaled) * 255), 'RGBA')
            if self.arrayparam:
                angle = np.angle(self.param[k][0][0], deg=True)
            else:
                angle = np.angle(self.param, deg=True)
            angle_str = f'{angle % 360:.02f}'.replace('.', '_')
            filename = f'fractal{k:04}_{angle_str}.png'
            im.save(relative('output', folder, filename))
            if animate:
                images.append(im)
        if animate:
            if len(images) > 1:
                save_gif(images, relative(folder, 'fractal_animated.gif'), seconds=seconds)
            else:
                print('Cannot animate as there is only one frame')

def save_gif(images, path, seconds=-1):
    for i in range(len(images)):
        images[i] = images[i].convert('P', palette=Image.ADAPTIVE)
    if seconds > 0:
        duration = seconds * 1000 / len(images)
    else:
        duration = 50
    images[0].save(path, save_all=True, append_images=images[1:], duration=duration, loop=0, disposal=2)

def gif_folder(folder, filename='fractal_animated.gif', seconds=0):
    if not os.path.isdir(folder):
        folder = relative('output', folder)
    images = []
    pngs = sorted(filter(lambda fn: os.path.splitext(fn)[1] == '.png', os.listdir(folder)))
    for fn in pngs:
        im = Image.open(os.path.join(folder, fn))
        images.append(im.convert('P', palette=Image.ADAPTIVE)) 
    save_gif(images, os.path.join(folder, filename), seconds=seconds)
 