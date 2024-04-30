from matplotlib import pyplot as plt
from matplotlib import figure
from pixel.router import router as rt
import os
from time import time
import sys


def draw(fig: figure.Figure):
    path = os.path.join(
        os.path.dirname(sys.argv[1]), 
        "static", 
        "file-{}.png".format(int(time() / 1000))
    )
    fig.savefig(path)
    rt.Router().add_img(1, path)
