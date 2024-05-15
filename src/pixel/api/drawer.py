from matplotlib import figure
from pixel.api.widgets import (
    Form,
    Html,
    ImageFile,
    Input,
    Markdown,
    Output,
    Row,
    Column,
)
from PIL import Image as PilImage
import imagehash
from pixel.web.processors import defaultProcessorManager as procManager
from pixel.widget_manager.widget_manager import defaultWidgetManager as widgetManager
import os
from time import time
import plotly as px
from pixel.commons import nextId
import hashlib

from pixel.variables import CommonVariables, VariablesNames


def pyplot(fig: figure.Figure, justCreate=False):
    filename = "file-{}.png".format(int(time() * 1000))

    path = os.path.join(CommonVariables.get_var(VariablesNames.STATIC_PATH), filename)

    fig.savefig(path)
    img = PilImage.open(path)
    imgHash = str(imagehash.average_hash(img))
    img.close()
    imgWidget = ImageFile(imgHash, filename) 
    if justCreate:
        return imgWidget
    else:
        widgetManager.register(imgHash, imgWidget)


def plotly(fig, justCreate=False):
    filename = "file-{}.html".format(int(time() * 1000))

    path = os.path.join(CommonVariables.get_var(VariablesNames.STATIC_PATH), filename)

    px.offline.plot(fig, filename=path, auto_open=False)
    hash = hashlib.md5(fig.to_json().encode()).hexdigest()

    if justCreate:
        return Html(hash, filename)
    else:
        widgetManager.register(hash, Html(hash, filename))


def title(text):
    CommonVariables.set_var(VariablesNames.TITLE, text)


def markdown(mdText, justCreate=False):
    widget = Markdown(hashlib.md5(mdText.encode()).hexdigest(), mdText)
    if justCreate:
        return widget 
    else:
        widgetManager.register(widget.hash, widget)

def row(widgets, justCreate=False):
    if justCreate:
        return Row(widgets)

    widgetManager.register(id, Row(widgets))


def column(widgets, justCreate=False):
    if justCreate:
        return Column(widgets)

    id = nextId()
    widgetManager.register(id, Column(widgets))

# TODO придумать как тут считать хеш
def form(inputWidgets, outputWidget: Output, function):
    try:
        iter(inputWidgets)
    except TypeError:
        inputWidgets = [inputWidgets]

    argsAmnt = function.__code__.co_argcount
    if len(inputWidgets) != argsAmnt:
        # TODO send alert or display error instead of this panel
        pass
    for inputElement in inputWidgets:
       if not issubclass(inputElement.__class__, Input):
            # TODO send alert or display error instead of this panel
            break
    if not issubclass(outputWidget.__class__, Output):
        # TODO send alert or display error instead of this panel
        pass

    procManager.registerNew('hash', function, outputWidget._type)
    widgetManager.register('hash', Form(inputWidgets, outputWidget))


