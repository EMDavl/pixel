import apispec
import json

from pixel.commons import Singleton
from pixel.variables import CommonVariables, VariablesNames
from pixel.web.processors import ProcessorsManager


class SpecGenerator(metaclass = Singleton):
    def __init__(self) -> None:
        self.spec = apispec.APISpec(title=CommonVariables.get_var(VariablesNames.TITLE), version="0.0.1", openapi_version='3.1.0')
        self.procManager = ProcessorsManager()
    
    def generate(self):
        for enpoint, processor in self.procManager.endpoints.items():
            request_schema = processor.request_specification()

            self.spec.path(
                path='/api' + enpoint,
                operations={
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": request_schema
                                }
                            },
                            "required": True
                            },
                        "responses": processor.response_specification()
                    }
                }
            )
        
        with open(CommonVariables.get_var(VariablesNames.SPEC_PATH), "w") as f:
            f.write(json.dumps(self.spec.to_dict()))
