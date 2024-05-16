from abc import ABCMeta, abstractmethod
import base64
from io import BytesIO
from typing import Any, Dict, Callable, Type

import jsonpickle

from pixel.api.widgets import WidgetType
from pixel.commons import Singleton
from pixel.web.exceptions import NotExists

from inspect import signature, getfullargspec
from pydantic import BaseModel, Field, create_model


class ProcessorsManager(metaclass=Singleton):
    def __init__(self):
        self.data: Dict[str, Processor] = {}

    def registerForm(self, formId, function, resultType):
        self.data[formId] = FormProcessor(formId, function, resultType)

    # TODO Если при перезапуске скрипта этого эндпоинта не нашлось, то нужно удалить
    def registerEndpoint(self, endpoint, function):
        self.data[endpoint] = EndpointProcessor(endpoint, function)

    def register(self, id, endpointProcessor):
        self.data[id] = endpointProcessor

    def process(self, id, args):
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
        if self._resultType == WidgetType.IMAGE_OUTPUT:
            buffered = BytesIO()
            result.save(buffered, format="PNG")
            imgStr = base64.b64encode(buffered.getvalue())
            return {
                "bytes": imgStr.decode("UTF-8"),
                "type": "form_response",
                "outputType": self._resultType.name,
                "formId": self._formId,
            }
        elif self._resultType == WidgetType.TEXT_OUTPUT:
            return {
                "text": str(result),
                "formId": self._formId,
                "type": "form_response",
                "outputType": self._resultType.name.lower(),
            }


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


class Result:
    def __init__(self, result) -> None:
        self.result = result


defaultProcessorManager = ProcessorsManager()