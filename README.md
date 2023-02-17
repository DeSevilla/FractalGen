A numpy-based fractal image generator, with support for single images or animations.
Can generate [Julia sets](https://en.wikipedia.org/wiki/Julia_set) and variations on the
[Mandelbrot set](https://en.wikipedia.org/wiki/Mandelbrot_set).

To set this up, install [Python 3.10](https://www.python.org/downloads/release/python-31010/).
Then navigate to this folder and run the command `python -m pip install -r requirements.txt` to install
all required libraries.

To test it out, you can run `python main.py default.yaml` or `python main.py default`.
Check out the yaml files in /configs for more examples of how it can be configured.
variable.yaml has some annotations to explain how variable parameters work with animations.
More formal information is below.

![spiraling tiled fractal](./example_images/julia_default.png)

usage: `python main.py [-h] [--random] [FILE]`

positional arguments:
  * FILE          optional name of a YAML config file within the /configs folder, e.g. default.yaml. The '.yaml' can be omitted.

options:
  * -h, --help    show a help message and exit
  * --random, -r  generate a random config file (with the filename specified by FILE or random.yaml if none)

If no configuration file is provided and --random is not used, it will prompt for a config file. 
The config used for a given run will be stored in its output folder, so it can be moved into the configs folder
to recreate that run if the original config file has changed or no longer exists.

Config parameters:

* Run parameters
  * run_type: String specifying what type of output we're producing. Options:
    * julia: generate a Julia set
    * mandelbrot: generate a Mandelbrot-like set. Will ignore the 'param' variable seen below.
    * reanimate: recreate the gif from a folder of .pngs. Does not run any further calculations
  * folder: a folder for the output. optional except with run_type = 'reanimate'

* Display parameters
  * pixels: integer by default, fills in values for xpixels and ypixels. Alternative parameters are:
    * xpixels: how many pixels wide the images should be
    * ypixels: how many pixels tall the images should be
  * frames: integer, how many frames to generate (if 1, will not animate)
  * seconds: float, how long the animation should be. Defaults to frames / 24.
  * colormap: string, name of a MatPlotLib colormap that defines how to color the display.
    See https://matplotlib.org/stable/tutorials/colors/colormaps.html for more options and info. 
    I like cm.inferno, cm.viridis, and cm.plasma; cm.prism is amusingly ugly.
  * color_by: string, specifies what data should be fed into the colormap. Options are:
    * iterations: color each point by how many iterations it lasted without diverging
    * diverged: how many iterations it took to diverge, or 0 if it didn't diverge
    * array: absolute value of each point (this will be the maximum value for any divergent point)
    * undiverged: absolute value of each undivergent point, or 0 for any divergent point
    * nested: how many iterations it took to diverge, or absolute value if it didn't diverge
  * normalize_frame_colors: True/False, whether to try to maintain consistent colors for 
    specific data values between frames.
    If the number of steps varies between frames and color_by is 'iterations', 
    having this as True will show undiverged points differently between different frames.

* Fixed simulation parameters
  * height: float, height of the viewing window in the complex plane. If you want this to change over animation, use zoom.
  * width: float, width of the viewing window. defaults to height times the ratio of xpixels to ypixels
  * center: complex number, center of the viewing window
  * point_value_max: float, maximum absolute value at any point


* Variable simulation parameters
  * These can be fixed or vary by frame. If they vary, they will be linearly interpolated frame-by-frame unless stated otherwise
  * steps: integer, how many steps to run for. Alternative parameters are:
    * steps_start: steps to run for the first frame
    * steps_end: steps to run for the last frame
  * zoom: float, the zoom of the window. Smaller values of this mean zooming out; larger values mean zooming in.
    Must be positive. Alternative parameters are:
    * zoom_start: zoom at the first frame
    * zoom_end: zoom at the last frame
  * shift: complex number, how much the window should be shifted (will be added to center). Alternative parameters are:
    * shift_start: shift at the first frame
    * shift_end: shift at the last frame
  * power: float, `p` in the step equation `x^p + c`. Alternative parameters are:
    * power_start: power at the first frame
    * power_end: power at the last frame
  * param: complex, `c` in the step equation `x^p + c`. Not applicable to Mandelbrot sets.
    Can be set directly, or by alternative parameters:
    * param_radius: float, distance of param from origin. Available both in fixed and variable modes
    * param_degrees: float, degrees of param relative to the positive real numbers. Fixed mode only. Alternative parameters are:
      * param_degrees_start: degrees of param at first frame. Variable mode only
      * param_degrees_end: degrees of param at last frame. Variable mode only
