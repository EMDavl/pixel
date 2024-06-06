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
        defs = "$defs"
        self.spec = apispec.APISpec(title=CommonVariables.get_var(VariablesNames.TITLE), version="0.0.1", openapi_version='3.1.0')
        for enpoint, processor in self.procManager.endpoints.items():
            request_schema = processor.request_schema()
            if request_schema.get(defs) is not None:
                for key, value in request_schema.get(defs).items():
                    self.spec.components.schema(key, value)
                request_schema.pop(defs)
            
            response_schema = processor.response_schema()
            if response_schema.get(defs) is not None:
                for key, value in response_schema.get(defs).items():
                    self.spec.components.schema(key, value)
                response_schema.pop(defs)
            
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
                        "responses": {
                            "200": {
                                "description": "response object",
                                "content": {
                                    "application/json": {
                                        "schema": response_schema
                                    }
                                }
                            }
                        }
                    }
                }
            )
        
        with open(CommonVariables.get_var(VariablesNames.SPEC_PATH), "w") as f:
            schema = json.dumps(self.spec.to_dict())
            schema = schema.replace(defs, "components/schemas")
            f.write(schema)