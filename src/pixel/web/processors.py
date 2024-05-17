from abc import ABCMeta, abstractmethod
import base64
from io import BytesIO
from typing import Any, Dict

import jsonpickle

from pixel.api.widgets import WidgetType
from pixel.commons import Singleton, WebSocketMessage, WebSocketMessageType
from pixel.dataclasses import ImageFormOutput, TextFormOutput
from pixel.web.exceptions import NotExists

from inspect import signature
from pydantic import Field, create_model
import apispec


class ProcessorsManager(metaclass=Singleton):
    def __init__(self):
        self.spec = apispec.APISpec(title="Your cool app", version="0.0.1", openapi_version='3.1.0')
        self.data: Dict[str, Processor] = {}

    def registerForm(self, formId, function, resultType):
        self.data[formId] = FormProcessor(formId, function, resultType)

    def registerEndpoint(self, endpoint, function):
        processor = EndpointProcessor(endpoint, function)
        self.data[endpoint] = processor
        # self.spec.path(
        #     processor.spec()
        # )

    def register(self, id, endpointProcessor):
        self.data[id] = endpointProcessor

    def processForm(self, id, args):
        return self.data[id].process(args)

    def processApi(self, id, body):
        processor = self.data.get(id)
        if processor is None:
            raise NotExists

        return self.data[id].process(body)


class Processor(metaclass=ABCMeta):

    @abstractmethod
    def process(self, requestBody) -> Any: ...


class FormProcessor(Processor):
    def __init__(self, formId, func, resultType):
        self._function = func
        self._resultType = resultType
        self._formId = formId

    def process(self, requestBody):
        result = self._function(*requestBody)
        msgBuilder = lambda x: WebSocketMessage(WebSocketMessageType.FORM_RESPONSE, x.to_message())
        if self._resultType == WidgetType.IMAGE_OUTPUT:
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            imgStr = base64.b64encode(buffered.getvalue())
            return msgBuilder(ImageFormOutput(self._formId, imgStr.decode("UTF-8")))

        elif self._resultType == WidgetType.TEXT_OUTPUT:
            return msgBuilder(TextFormOutput(self._formId, str(result)))


class EndpointProcessor(Processor):

    def __init__(self, endpoint, func):
        self._function = func
        modelFields = {}
        self._functionParams = []
        for key, val in signature(func).parameters.items():
            modelFields[val.name] = (val.annotation, Field())
            self._functionParams.append(key)
        self._pydanticModel = create_model(endpoint, **modelFields)

    def process(self, requestBody):
        model = self._pydanticModel(**jsonpickle.decode(requestBody))
        result = self._function(**vars(model))
        return self._getResult(result)

    def _getResult(self, data):
        primitives = (bool, str, int, float, type(None), list, set)
        if isinstance(data, primitives):
            return Result(data)
        return data
    
    def spec(self):
        return ""


class Result:
    def __init__(self, result) -> None:
        self.result = result


defaultProcessorManager = ProcessorsManager()
