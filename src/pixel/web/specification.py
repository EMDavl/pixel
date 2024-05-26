import apispec
import json

from pixel.variables import CommonVariables, VariablesNames
from pixel.web.processors import ProcessorsManager


class SpecGenerator():
    def __init__(self) -> None:
        self.spec = apispec.APISpec(title=CommonVariables.get_var(VariablesNames.TITLE), version="0.0.1", openapi_version='3.1.0')
        self.procManager = ProcessorsManager()
    
    def generate(self):
        for enpoint, processor in self.procManager.endpoints.items():
            jsonschema = processor.specBody()
            # definitions = jsonschema["$defs"]
            # jsonschema.pop('$defs')
            # print(definitions)
            # for componentId, componentDefinition in definitions.items():
                # self.spec.components.schema(componentId, componentDefinition)
            # jsonschema['properties']['data']['$ref'] = "#/components/schemas/Data"
            self.spec.path(
                path='/api' + enpoint,
                operations={
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": jsonschema
                                }
                            },
                            "required": True
                            },
                        "responses": processor.specResponse()
                    }
                }
            )
        
        with open(CommonVariables.get_var(VariablesNames.SPEC_PATH), "w") as f:
            f.write(json.dumps(self.spec.to_dict()))

