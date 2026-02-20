import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from puppets.environment_service.runtime import ContainerRuntime

@pytest.fixture
def runtime():
    with patch("shutil.which", return_value="/usr/bin/podman"):
        return ContainerRuntime()

def test_detect_runtime_podman():
    with patch("shutil.which", side_effect=lambda x: "/usr/bin/podman" if x == "podman" else None):
        cr = ContainerRuntime()
        assert cr.runtime == "podman"

def test_detect_runtime_docker():
    with patch("shutil.which", side_effect=lambda x: "/usr/bin/docker" if x == "docker" else None):
        cr = ContainerRuntime()
        assert cr.runtime == "docker"

def test_detect_runtime_none():
    with patch("shutil.which", return_value=None):
        cr = ContainerRuntime()
        assert cr.runtime == "subprocess"

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_run_subprocess_fallback(runtime):
    runtime.runtime = "subprocess"
    result = await runtime.run("alpine", ["echo", "hi"])
    assert result["exit_code"] == -1
    assert "Container Runtime not found" in result["stderr"]

@pytest.mark.anyio
async def test_run_podman_command_gen(runtime):
    runtime.runtime = "podman"
    
    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock()
    mock_proc.communicate.return_value = (b"output", b"error")
    mock_proc.returncode = 0
    
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        await runtime.run(
            image="alpine", 
            command=["echo", "hi"],
            env={"FOO": "BAR"},
            mounts=["/src:/dest:ro"],
            input_data="input"
        )
        
        # Verify podman specific flags
        args, kwargs = mock_exec.call_args
        assert "podman" in args
        assert "--userns=keep-id" in args
        assert "-e" in args
        assert "FOO=BAR" in args
        assert "-v" in args
        assert "/src:/dest:ro" in args
