from _plotly_utils.basevalidators import base64
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
from pixel.web.processors import defaultProcessorManager as procManager
from pixel.widget_manager.widget_manager import defaultWidgetManager as widgetManager
import os
from time import time
import plotly as px
from io import BytesIO

from pixel.variables import CommonVariables, VariablesNames


def pyplot(fig: figure.Figure, justCreate=False):
    filename = "file-{}.png".format(int(time() * 1000))

    path = os.path.join(CommonVariables.get_var(VariablesNames.STATIC_PATH), filename)

    fig.savefig(path)
    if justCreate:
        return ImageFile(None, filename)
    else:
        id = next(generator)
        widgetManager.register(id, ImageFile(id, filename))


def plotly(fig, justCreate=False):
    filename = "file-{}.html".format(int(time() * 1000))

    path = os.path.join(CommonVariables.get_var(VariablesNames.STATIC_PATH), filename)

    px.offline.plot(fig, filename=path, auto_open=False)

    if justCreate:
        return Html(None, filename)
    else:
        id = next(generator)
        widgetManager.register(id, Html(id, filename))


def title(text):
    CommonVariables.set_var(VariablesNames.TITLE, text)


def markdown(mdText, justCreate=False):
    if justCreate:
        return Markdown(None, mdText)
    else:
        id = next(generator)
        widgetManager.register(id, Markdown(id, mdText))


def row(widgets, justCreate=False):
    if justCreate:
        return Row(None, widgets)

    id = next(generator)
    widgetManager.register(id, Row(id, widgets))


def column(widgets, justCreate=False):
    if justCreate:
        return Column(None, widgets)

    id = next(generator)
    widgetManager.register(id, Column(id, widgets))


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
        if inputElement._id is None:
            inputElement._id = next(generator)
        if not issubclass(inputElement.__class__, Input):
            # TODO send alert or display error instead of this panel
            break
    if not issubclass(outputWidget.__class__, Output):
        # TODO send alert or display error instead of this panel
        pass
    if outputWidget._id is None:
        outputWidget._id = next(generator)
    identifier = next(generator)

    procManager.registerNew(identifier, function, outputWidget.outputType)
    widgetManager.register(identifier, Form(identifier, inputWidgets, outputWidget))


def get_id():
    id = 0
    while True:
        id = id + 1
        yield id


generator = get_id()
