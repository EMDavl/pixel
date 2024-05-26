from abc import ABCMeta, abstractmethod
import base64
from io import BytesIO
from typing import Any, Dict

import jsonpickle

from pixel.api.widgets import Output, WidgetType
from pixel.commons import Singleton, WebSocketMessage, WebSocketMessageType
from pixel.dataclasses import ImageFormOutput, TextFormOutput
from pixel.web.exceptions import NotExists

from inspect import signature
from pydantic import BaseModel, Field, create_model


class ProcessorsManager(metaclass=Singleton):

    def __init__(self):
        self.forms: Dict[str, Processor] = {}
        self.endpoints: Dict[str, Processor] = {}

    def registerForm(self, formId, function, resultType):
        self.forms[formId] = FormProcessor(formId, function, resultType)

    def registerEndpoint(self, endpoint, function, outputType):
        processor = EndpointProcessor(endpoint, function, outputType)
        self.endpoints[endpoint] = processor

    def register(self, id, endpointProcessor):
        self.forms[id] = endpointProcessor

    def processForm(self, id, args):
        return self.forms[id].process(args)

    def processApi(self, id, body):
        processor = self.endpoints.get(id)
        if processor is None:
            raise NotExists

        return processor.process(body)


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

    def __init__(self, endpoint, func, outputType):
        self._function = func
        modelFields = {}
        self._functionParams = []
        for key, val in signature(func).parameters.items():
            modelFields[val.name] = (val.annotation, Field())
            self._functionParams.append(key)
        self._pydanticModel = create_model(endpoint, **modelFields)
        self.endpoint = endpoint
        self.outputType = outputType

    def process(self, requestBody):
        model = self._pydanticModel(**jsonpickle.decode(requestBody))
        result = self._function(**vars(model))
        return self._getResult(result)

    def _getResult(self, data):
        primitives = (bool, str, int, float, type(None), list, set)
        if isinstance(data, primitives):
            return Result(data)
        return data
    
    def specBody(self):
        return self._pydanticModel.model_json_schema()
    
    def specResponse(self):
        strRespSchema = {
            "type": "object",
            "required": [
                "result"
            ],
            "properties": {
                "result": {
                    "type": "string"
                }
            }
        }
        responseSchema = self.outputType.model_json_schema() if issubclass(self.outputType, BaseModel) else strRespSchema
        return {
            "200": {
                "content": {
                    "application/json": {
                        "schema": responseSchema
                    }
                }
            }
        }
   
class Result:
    def __init__(self, result) -> None:
        self.result = result


defaultProcessorManager = ProcessorsManager()
