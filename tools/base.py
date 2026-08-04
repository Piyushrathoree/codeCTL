import abc
from  __future__ import annotations
from  enum import Enum
from  typing import Any
from pydantic import BaseModel, ValidationError
from dataclasses import dataclass, field
from pathlib import Path

class  ToolKind(str ,Enum):
    READ = "read"
    WRITE= "write"
    SHELL =  "shell"
    NETWORK = "network"
    MEMORY = "memory"
    MCP =  "mcp"

@dataclass 
class ToolInvocation:
    cwd :  Path
    params: dict[str,Any]

@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    metadata:dict[str,Any] = field(default_factory=dict)



class Tool(abc.ABC):
    name: str = "base_tool"
    description:str = "Base tool"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        super().__init__()

    @property
    def schema(self)  -> dict[str,Any] | type['BaseModel']:
        raise NotImplementedError("tools must define a schema property  or  class attribute")

    @abc.abstractmethod
    async  def execute  (self,invocation:ToolInvocation) -> ToolResult:
        pass

    def   validate_params(self,params:dict[str,Any]) -> list[str]:
        schema = self.schema
        if isinstance(schema,type) and issubclass(schema,BaseModel):
            try:
                schema(**params)
            except ValidationError as e:
                 error = []
                 for  error  in  e.errors():
                    field = ".".join(str(x) for x in  error('loc',[]))