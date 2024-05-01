from matplotlib import figure
from pixel.api.widgets import Html, Image
from pixel.router import router as rt
import os
from time import time
import plotly as px

from pixel.variables import CommonVariables, VariablesNames

def pyplot(fig: figure.Figure):
    filename = "file-{}.png".format(int(time() * 1000))

    path = os.path.join(
        CommonVariables.get_var(VariablesNames.STATIC_PATH),
        filename)

    fig.savefig(path)
    id = next(generator)
    rt.Router().add(id, Image(id, filename))

def plotly(fig):
    filename = "file-{}.html".format(int(time() * 1000))

    path = os.path.join(
        CommonVariables.get_var(VariablesNames.STATIC_PATH),
        filename)

    px.offline.plot(fig, filename=path, auto_open=False)
    id = next(generator)
    rt.Router().add(id, Html(id, filename))

def page_title(text):
    # TODO Добавить установку кастомного заголовка странице, можно использовать template'ы торнадо
    pass

def get_id():
    id = 0
    while True:
        id = id + 1
        yield id

generator = get_id()
