

from pixel.variables import CommonVariables, VariablesNames

# TODO Maybe we should execute script in another thread?
async def execute_script():
    with open(CommonVariables.get_var(VariablesNames.SCRIPT_NAME)) as f:
        file = f.read()
    
    bytecode = compile(file, mode="exec", filename=CommonVariables.get_var(VariablesNames.SCRIPT_NAME))
    exec(bytecode, globals())