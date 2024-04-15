import json
from typing import Any
from pydantic import BaseModel
from varname import varname
import inspect


class Task(BaseModel):
    name: str
    parameters: list

building = False


class HeraInput(BaseModel):

    def __init__(self, /, **data: Any) -> None:
        if not building: 
            super().__init__(**data)
        else:
            object.__setattr__(self, "_p_data", data)
        
        
    def __getattr__(self, __name: str) -> Any:
        if building and __name != "_p_data" and __name in object.__getattribute__(self, "_p_data"):
            value = self._p_data[__name]
            if isinstance(value, str):
                return value
            if isinstance(value, BaseModel):
                return value.model_dump_json()
            return json.dumps(value)
        return super().__getattr__(__name)
        
class _HeraBuildOutput:

    def __init__(self, output_class: BaseModel, type_: str, name: str) -> None:
        self._output_class = output_class
        self._type = type_
        self._name = name

    def _get_var_type(self, name: str) -> str:
        # figure out if its an artifact or parameter from the given output basemodel type
        return "parameters"
    
    def _get_var_name(self, name: str) -> str:
        # figure out aliases from the given output basemodel type
        return name
         
    def __getattribute__(self, __name: str) -> Any:
        if not __name.startswith("_"):
            return f"{self._type}.{self._name}.{self._get_var_type(__name)}.{self._get_var_name(__name)}"
        return object.__getattribute__(self, __name)


class HeraOutput(BaseModel):
    ...

class Script(BaseModel):
    name: str
    
    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
    
    def __call__(self, name:str, *args: Any, **kwds: Any) -> Any:
        return Task(name=name)

class WorkflowTemplate(BaseModel):
   
    def __init__(self, /, **data: Any) -> None:
        super().__init__(**data)
        self._building = False
        self._templates = []
        self._tasks = []

    def script(self, *args, **kwargs):
        def wrapper(f):
            signature = inspect.signature(f)
            outputs = signature.return_annotation
            inputs = signature.parameters['in_'].annotation
            s = Script(name=f.__name__)
            self._templates.append(s)
            def wrapped(*args, **kwargs):
                if building:
                    name = kwargs.pop("name", varname())
                    params = []
                    for key in args[0]._p_data:
                        params.append({
                            "name": key,
                            "value": getattr(args[0], key)
                        })
                    self._tasks.append(Task(name=name, parameters=params))
                    return _HeraBuildOutput(output_class=outputs, name=name, type_="tasks")
                return f(*args, **kwargs)
            return wrapped
        return wrapper
                
        

wt = WorkflowTemplate()

class Input(HeraInput):
    x: int
    

class Output(HeraOutput):
    x: int

@wt.script()
def example(in_: Input) -> Output:
    return Output(x=in_.x)

x = example(Input(x=1))
print(x)
building = True
y = example(Input(x=1))
print(y.x)
asd = example(Input(x=y.x))
asd2 = example(Input(x=1), name="foo")
print(wt._tasks)
