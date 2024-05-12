import base64
from io import BytesIO
from typing import Any, Dict

from pixel.commons import Singleton

class ProcessorsManager(metaclass=Singleton):
    def __init__(self):
        self.data: Dict[int, EndpointProcessor] = {}

    def registerNew(self, id, function, resultType):
        self.data[id] = EndpointProcessor(id, function, resultType)

    def register(self, id, endpointProcessor):
        self.data[id] = endpointProcessor
    
    def process(self, id, args) -> Dict[str, Any]:
        return self.data[id].process(args)

class EndpointProcessor:
    def __init__(self, formId, func, resultType):
        self._function = func
        self._resultType = resultType
        self._formId = formId

    def process(self, args) -> Dict[str, Any]:
        result = self._function(*args)
        buffered = BytesIO()
        if (self._resultType == "image_output"):
            result.save(buffered, format="PNG")
            imgStr = base64.b64encode(buffered.getvalue())
            return {
                "bytes": imgStr.decode("UTF-8"),
                "type": "form_response",
                "outputType": self._resultType,
                "formId": self._formId,
                }
        elif (self._resultType == "text_output"):
            return {
                "text": str(result),
                "formId": self._formId,
                "type": "form_response",
                "outputType": self._resultType,
            }
        return {}

defaultProcessorManager = ProcessorsManager()