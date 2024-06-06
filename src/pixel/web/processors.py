from abc import ABCMeta, abstractmethod
import base64
from concurrent.futures import process
from io import BytesIO
from typing import Any, Dict

import jsonpickle

from pixel.api.widgets import Output, WidgetType
from pixel.commons import Singleton, WebSocketMessage, WebSocketMessageType
from pixel.dataclasses import ImageFormOutput, TextFormOutput
from pixel.web.exceptions import NotExists
from typing import get_type_hints

from inspect import signature
from pydantic import BaseModel, Field, create_model


class ProcessorsManager(metaclass=Singleton):

    def __init__(self):
        self.forms: Dict[str, Processor] = {}
        self.endpoints: Dict[str, Processor] = {}
        self.script_running = False
        self.forms_sn = {}
        self.endpoints_sn = {}

    def registerForm(self, formId, function, resultType):
        self.forms[formId] = FormProcessor(formId, function, resultType)

    def registerEndpoint(self, endpoint, function, outputType):
        processor = EndpointProcessor(endpoint, function, outputType)
        self.endpoints[endpoint] = processor

    def register(self, id, endpointProcessor):
        self.forms[id] = endpointProcessor

    def processForm(self, id, args):
        form = self.forms_sn.get(id) if self.script_running else self.forms_sn.get(id)

        if form is None:
            raise NotExists

        return form.process(args)

    def processApi(self, id, body):
        processor = (
            self.endpoints_sn.get(id) if self.script_running else self.endpoints.get(id)
        )
        if processor is None:
            raise NotExists

        return processor.process(body)

    def snapshot(self):
        self.script_running = True
        self.endpoints_sn = self.endpoints
        self.forms_sn = self.forms
        self.forms = {}
        self.endpoints = {}
        return ProcessorsManagerSnapshot(self.forms_sn, self.endpoints_sn)
    
    def executed(self):
        self.script_running = False


class ProcessorsManagerSnapshot:

    def __init__(self, forms_sn, endpoints_sn):
        self.forms_sn = forms_sn
        self.endpoints_sn = endpoints_sn


    def has_diff(self):

        self.endpoints = defaultProcessorManager.endpoints
        self.forms = defaultProcessorManager.forms

        if len(self.endpoints_sn) != len(self.endpoints) or len(self.forms_sn) != len(
            self.forms
        ):
            print("step 1")
            return True


        for endpoint, processor in self.endpoints_sn.items():
            new_proc = self.endpoints.get(endpoint)
            if new_proc is None:
                print("step 2")
                return True

            if not self.compare_pydantic_models(new_proc._pydanticModel, processor._pydanticModel):
                print("step 3")
                return True
            
            old_output = processor.outputType 
            new_output = new_proc.outputType  
            if old_output != new_output:
                if issubclass(old_output, BaseModel) and issubclass(new_output, BaseModel) and self.compare_pydantic_models(old_output, new_output):
                    continue
                print("step 4")
                return True

        return False
    
    def compare_pydantic_models(self, model1: BaseModel, model2: BaseModel) -> bool:
        hints1 = get_type_hints(model1)
        hints2 = get_type_hints(model2)
    
        if hints1.keys() != hints2.keys():
            return False
    
        for key in hints1:
            type1 = hints1[key]
            type2 = hints2[key]
        
            if type1 != type2:
                # Если тип поля является моделью Pydantic, сравниваем их рекурсивно
                if issubclass(type1, BaseModel) and issubclass(type2, BaseModel):
                    if not self.compare_pydantic_models(type1, type2):
                        print("Here")
                        return False
                else:
                    return False

        # Сравнение значений по умолчанию
        defaults1 = {k: v.default for k, v in model1.__fields__.items()}
        defaults2 = {k: v.default for k, v in model2.__fields__.items()}
    
        if defaults1 != defaults2:
            return False
    
        return True

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
        msgBuilder = lambda x: WebSocketMessage(
            WebSocketMessageType.FORM_RESPONSE, x.to_message()
        )
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
        elif isinstance(data, BaseModel):
            return data.model_dump()
        return Result("empty")

    def request_schema(self):
        return self._pydanticModel.schema()

    def response_schema(self):
        strRespSchema = {
            "type": "object",
            "required": ["result"],
            "properties": {"result": {"type": "string"}},
            "example": {"result": "string"},
        }
        response_schema = (
            self.outputType.schema()
            if issubclass(self.outputType, BaseModel)
            else strRespSchema
        )
        return response_schema


class Result:
    def __init__(self, result) -> None:
        self.result = result


defaultProcessorManager = ProcessorsManager()
