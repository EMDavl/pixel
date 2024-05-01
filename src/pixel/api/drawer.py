from matplotlib import figure
from pixel.router import router as rt
import os
from time import time

from pixel.variables import CommonVariables, VariablesNames

def pyplot(fig: figure.Figure):
    filename = "file-{}.png".format(int(time() * 1000))

    path = os.path.join(
        CommonVariables.get_var(VariablesNames.STATIC_PATH),
        filename)

    fig.savefig(path)
    rt.Router().add_img(next(get_id()), filename)

def page_title(text):
    # TODO Добавить установку кастомного заголовка странице
    pass

def get_id():
    id = 0
    while True:
        yield (id := id + 1)