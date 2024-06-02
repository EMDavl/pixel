import functools
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
from pixel.cache.cache_manager import CacheManager
from pixel.web.processors import defaultProcessorManager as procManager
from pixel.widget_manager.widget_manager import defaultWidgetManager as widgetManager
import os
from time import time
import plotly as px
from matplotlib import pyplot as plt
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
    plt.close(fig) 
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
    elementHash = widgetManager.get_id(hashlib.md5(mdText.encode()).hexdigest())

    widget = Markdown(elementHash, mdText)
    if justCreate:
        return widget
    else:
        widgetManager.register(widget.hash, widget)


def row(widgets, justCreate=False):
    row = Row(widgets)
    if justCreate:
        return row

    widgetManager.register(row.hash, row)


def column(widgets, justCreate=False):
    col = Column(widgets)
    if justCreate:
        return col

    widgetManager.register(col.hash, col)


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
    form = Form(inputWidgets, outputWidget)
    procManager.registerForm(form.id, function, outputWidget._type)
    widgetManager.register(form.hash, form)


def api(endpoint, outputType):
    def wrap(func):
        procManager.registerEndpoint(endpoint, func, outputType)

        @functools.wraps(func)
        def wrapper(*args):
            return func(*args)

        return wrapper

    return wrap

def endpoint(endpoint, outputType, func):
    procManager.registerEndpoint(endpoint, func, outputType)

def reusable(func):
    CacheManager.register_function(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return get_reusable(func, *args, **kwargs)
    
    return wrapper

def get_reusable(func, *args, **kwargs):
    result = CacheManager.get(func, *args, **kwargs)
    if result is None:
        result = func(*args, **kwargs)
        CacheManager.put(func, result, *args, **kwargs)
    return result
 