from pathlib import Path
from utils.paths import resolve_path
from pydantic import BaseModel, Field
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class ReadFileParams(BaseModel):
    path: str = Field(
        ...,
        description="The path to the file to read (related to working directory   or  absolute)",
    )
    offset: int = Field(
        1,
        ge=1,
        description="line number   to  start  reading  from  (1-based)  defalt  to  1",
    )
    limit: int | None = Field(
        None,
        ge=1,
        description="maximum number of lines to read. If not provided, all lines will be read.",
    )


class ReadFileTool(Tool):
    name: str = "read_file"
    description = (
        "read the content of a text file. Returns the file content with line numbers."
        "for large files,use offset and limit to read a specific portions"
        "Cannot read binary files (images, executables,etc.)"
    )
    kind = ToolKind.READ

    schema = ReadFileParams
    default_line_limit = 500

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)

        try:
            file_path = resolve_path(invocation.cwd, params.path)
        except ValueError as error:
            return ToolResult(
                success=False,
                output="",
                error=str(error),
            )
        if not file_path.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File {file_path} does not exist",
            )
        if not file_path.is_file():
            return ToolResult(
                success=False,
                output="",
                error=f"File {file_path} is not a file",
            )
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read file :{params.path}",
            )
        except OSError:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read file :{error}",
            )
        start_index = params.offset - 1
        if start_index >= len(lines):
            return ToolResult(
                success=False,
                output="",
                error=f"offset {params.offset} is out of range for file {params.path}",
            )
        line_limit = params.limit or self.default_line_limit
        selected_lines = lines[start_index : start_index + line_limit]
        output = "\n".join(
            f"{line_number:>6}\t{line}"
            for line_number, line in enumerate(selected_lines, start=params.offset)
        )

        return ToolResult(
            success=True,
            output=output,
            metadata={
                "path": str(file_path),
                "lines_returned": len(selected_lines),
                "truncated": start_index + len(selected_lines) < len(lines),
            },
        )
