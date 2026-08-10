from __future__ import annotations
import abc
from enum import Enum
from typing import Any
from pydantic import BaseModel, ValidationError
from dataclasses import dataclass, field
from pathlib import Path

from pydantic.json_schema import model_json_schema


class ToolKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    NETWORK = "network"
    MEMORY = "memory"
    MCP = "mcp"


@dataclass
class ToolInvocation:
    cwd: Path
    params: dict[str, Any]


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolConfirmation:
    tool_name: str
    params: dict[str, Any]
    description: str


class Tool(abc.ABC):
    name: str = "base_tool"
    description: str = "Base tool"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        super().__init__()

    @property
    def schema(self) -> dict[str, Any] | type["BaseModel"]:
        raise NotImplementedError(
            "tools must define a schema property  or  class attribute"
        )

    @abc.abstractmethod
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        pass

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        schema = self.schema

        #  this  is  pydantic  validation customized according  to  us
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                schema(**params)
            except ValidationError as error:
                errors: list[str] = []

                for item in error.errors():
                    field = ".".join(str(part) for part in item.get("loc", []))
                    message = item.get("msg", "validation error")
                    errors.append(f"{field}: {message}")

                return errors
            except Exception as e:
                return [str(e)]

    def is_mutating(self, params: dict[str, Any]) -> bool:
        return self.kind in {
            ToolKind.WRITE,
            ToolKind.SHELL,
            ToolKind.NETWORK,
            ToolKind.MEMORY,
        }

    def get_confirmation(self, invocation: ToolInvocation) -> ToolInvocation:
        if not self.is_mutating(invocation.params):
            return None

        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.params,
            description=f"Execute  {self.name}",
        )

    def to_openai_schema(self) -> dict[str, Any]:
        schema = self.schema

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            json_schema = model_json_schema(schema, mode="serialization")
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }

        if isinstance(schema, dict):
            result = {
                "name": self.name,
                "description": self.description,
            }
            if "parameters" in schema:
                result["parameters"] = schema["parameters"]
            else:
                result["parameters"] = schema
            return result

        #  if it is  not a  BaseModel or  a  dict,  it will  raise  a  ValueError
        raise ValueError(
            f"Invalid schema  type  for tool  {self.name} : {type(schema)}"
        )
