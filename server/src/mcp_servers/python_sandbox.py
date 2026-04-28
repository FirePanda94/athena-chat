import docker
import tempfile
import os
from fastmcp import FastMCP

mcp = FastMCP("python-sandbox")

@mcp.tool()
def run_python_code(code: str, packages: list[str] = []) -> str:
    """Run Python code in an isolated Docker container and return the output."""
    client = docker.from_env(timeout=60)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        # Build the command — install packages first if needed
        if packages:
            pip_install = f"pip install -q {' '.join(packages)} && "
        else:
            pip_install = ""

        result = client.containers.run(
            image="python:3.11-slim",
            command=f"bash -c \"{pip_install}python /code.py\"",
            volumes={tmp_path: {"bind": "/code.py", "mode": "ro"}},
            remove=True,
            mem_limit="256m",
            stdout=True,
            stderr=True,
        )
        return result.decode("utf-8")
    except docker.errors.ContainerError as e:
        return f"Error:\n{e.stderr.decode('utf-8')}"
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    mcp.run(transport="stdio")