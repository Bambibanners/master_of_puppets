import pytest
import asyncio
import json
import os
import base64
from unittest.mock import patch, MagicMock, AsyncMock
from puppets.environment_service.node import Node

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def mock_node_env(tmp_path):
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    
    with patch("puppets.environment_service.node.Node.bootstrap_trust"), \
         patch("puppets.environment_service.node.Node.ensure_identity"), \
         patch("puppets.environment_service.node.Node.fetch_verification_key"), \
         patch("puppets.environment_service.node.os.makedirs"):
         
        node = Node("https://localhost:8001", "test-node")
        node.cert_file = str(secrets_dir / "node.crt")
        node.key_file = str(secrets_dir / "node.key")
        node.verify_key_path = str(secrets_dir / "verification.key")
        node.join_token = "dummy-token"
        
        # Identity files
        with open(node.cert_file, "w") as f: f.write("CERT")
        with open(node.key_file, "w") as f: f.write("KEY")
        
        return node

@pytest.mark.anyio
async def test_poll_for_work(mock_node_env):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"job": {"guid": "job1"}}
    
    # Mock AsyncClient as a context manager
    with patch("puppets.environment_service.node.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client_class.return_value = mock_client
        
        work = await mock_node_env.poll_for_work()
        assert work["job"]["guid"] == "job1"

@pytest.mark.anyio
async def test_report_result(mock_node_env):
    with patch("puppets.environment_service.node.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post = AsyncMock()
        mock_client_class.return_value = mock_client
        
        await mock_node_env.report_result("job1", True, {"out": "ok"})
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert "/work/job1/result" in args[0]
        assert kwargs["json"]["success"] is True

def test_run_python_script_local(mock_node_env):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")
        res = mock_node_env.run_python_script("job1", "print('hello')")
        assert res["exit_code"] == 0
        assert res["stdout"] == "hello"

def test_bootstrap_trust_logic(tmp_path):
    # Testing the logic of bootstrap_trust directly
    ca_content = "-----BEGIN CERTIFICATE-----\nABC\n-----END CERTIFICATE-----"
    token_dict = {"t": "real-token", "ca": ca_content}
    encoded = base64.b64encode(json.dumps(token_dict).encode()).decode()
    
    with patch("puppets.environment_service.node.Node.ensure_identity"), \
         patch("puppets.environment_service.node.Node.fetch_verification_key"):
        
        node = Node("url", "nodeid")
        node.join_token = encoded
        
        # Point secrets/root_ca.crt to a tmp path by mocking open for that specific file
        # or just let it write if we are in a safe env, but better mock it.
        with patch("puppets.environment_service.node.open", create=True) as mock_open:
            node.bootstrap_trust()
            assert node.join_token == "real-token"
            # Verify CA content was saved
            # mock_open(root_ca_dest, "w")
            # We can check calls
