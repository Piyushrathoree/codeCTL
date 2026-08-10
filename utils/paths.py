from pathlib import Path

def resolve_path(base :str | Path, path :str | Path) -> Path:
    base_path = Path(base).resolve()
    requested_path = Path(path)

    if requested_path.is_absolute():
        resolved_path = requested_path.resolve()
    else:
        resolved_path = (base_path / requested_path).resolve()

    try:
        resolved_path.relative_to(base_path)
    except ValueError as error:
        raise ValueError(f"Path {requested_path} is not a subpath of {base_path}") from error

    return resolved_path
