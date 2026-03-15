import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agent_service.services.mirror_service import MirrorService
from agent_service.db import ApprovedIngredient


@pytest.mark.asyncio
async def test_mirror_pypi_command_construction():
    """Verify pip download command is correctly constructed."""
    mock_db = AsyncMock()
    ingredient = ApprovedIngredient(
        id="test-id",
        name="requests",
        version_constraint="==2.20.0",
        os_family="DEBIAN"
    )

    with patch("subprocess.run") as mock_run, patch("os.makedirs"):
        mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")

        await MirrorService._mirror_pypi(mock_db, ingredient)

        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert "pip" in cmd
        assert "download" in cmd
        assert "requests==2.20.0" in cmd
        assert "--dest" in cmd
        assert "--no-deps" in cmd


@pytest.mark.asyncio
async def test_mirror_ingredient_orchestration():
    """Verify mirror_ingredient updates DB status to MIRRORED on success."""
    ingredient = ApprovedIngredient(
        id="test-id",
        name="flask",
        version_constraint="==2.0.0",
        os_family="DEBIAN",
        mirror_status="PENDING"
    )

    with patch("agent_service.services.mirror_service.AsyncSessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = ingredient
        mock_db.execute.return_value = mock_res

        with patch.object(MirrorService, "_mirror_pypi", new_callable=AsyncMock):
            await MirrorService.mirror_ingredient("test-id")

            assert ingredient.mirror_status == "MIRRORED"
            mock_db.commit.assert_called()


def test_pip_conf_generation():
    """Verify pip.conf content points to correct host."""
    with patch.dict("os.environ", {"PYPI_MIRROR_URL": "http://my-pypi:8080/simple"}):
        content = MirrorService.get_pip_conf_content()
        assert "http://my-pypi:8080/simple" in content
        assert "trusted-host = my-pypi" in content


@pytest.mark.asyncio
async def test_mirror_pypi_log_capture():
    """Verify ingredient.mirror_log is set to combined stdout+stderr after _mirror_pypi."""
    mock_db = AsyncMock()
    ingredient = ApprovedIngredient(
        id="test-id",
        name="numpy",
        version_constraint="==1.24.0",
        os_family="DEBIAN",
        mirror_status="PENDING"
    )

    with patch("subprocess.run") as mock_run, patch("os.makedirs"):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Successfully downloaded numpy-1.24.0\n",
            stderr="WARNING: some warning\n"
        )

        await MirrorService._mirror_pypi(mock_db, ingredient)

        assert ingredient.mirror_log is not None, "mirror_log was not set"
        assert "numpy" in ingredient.mirror_log or "stdout" in ingredient.mirror_log.lower()
        assert "stderr" in ingredient.mirror_log.lower() or "WARNING" in ingredient.mirror_log


@pytest.mark.asyncio
async def test_mirror_ingredient_failure():
    """Verify mirror_ingredient sets mirror_status=FAILED when _mirror_pypi raises."""
    ingredient = ApprovedIngredient(
        id="fail-id",
        name="nonexistent-pkg",
        version_constraint="==99.99.99",
        os_family="DEBIAN",
        mirror_status="PENDING"
    )

    with patch("agent_service.services.mirror_service.AsyncSessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = ingredient
        mock_db.execute.return_value = mock_res

        with patch.object(MirrorService, "_mirror_pypi", new_callable=AsyncMock) as mock_pypi:
            mock_pypi.side_effect = Exception("pip download failed: no matching distribution")
            await MirrorService.mirror_ingredient("fail-id")

            assert ingredient.mirror_status == "FAILED", f"Expected FAILED, got {ingredient.mirror_status}"
            mock_db.commit.assert_called()


def test_sources_list_generation():
    """Verify get_sources_list_content returns a valid deb line with trusted=yes."""
    with patch.dict("os.environ", {"APT_MIRROR_URL": "http://my-mirror/apt"}):
        content = MirrorService.get_sources_list_content()
        assert "deb [trusted=yes]" in content
        assert "http://my-mirror/apt" in content
