import shutil
import subprocess
import os
import logging
import asyncio
from typing import Dict, List, Optional

class ContainerRuntime:
    def __init__(self):
        self.runtime = self.detect_runtime()
        logging.info(f"Container Runtime Detected: {self.runtime}")

    def detect_runtime(self) -> str:
        # In DinD environments prefer direct execution to avoid cgroup issues
        if os.path.exists("/.dockerenv"):
            return "direct"
        if os.path.exists("/var/run/docker.sock") and shutil.which("docker"):
            return "docker"
        if shutil.which("podman"):
            return "podman"
        if shutil.which("docker"):
            return "docker"
        return "direct"

    async def run(
        self, 
        image: str, 
        command: List[str], 
        env: Dict[str, str] = {}, 
        mounts: List[str] = [], 
        network_ref: str = None,
        input_data: str = None
    ) -> Dict:
        """
        Executes a containerized job.
        network_ref: ID/Hostname of the container to share network with (for Sidecar access).
        """
        
        if self.runtime == "direct":
            # Execute script directly in node process environment (DinD fallback)
            import sys
            merged_env = {**os.environ, **env}
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-",
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=merged_env
            )
            stdout, stderr = await proc.communicate(input=input_data.encode() if input_data else None)
            return {"exit_code": proc.returncode, "stdout": stdout.decode(), "stderr": stderr.decode()}

        cmd = [self.runtime, "run", "--rm"]
        if input_data:
            cmd.append("-i")

        # 1. Network Strategy
        if os.name != 'nt':
            cmd.extend(["--network=host"])

        # 2. Namespace Mapping (Podman specific)
        if self.runtime == "podman":
            cmd.append("--userns=keep-id")
            cmd.append("--storage-driver=vfs")
            cmd.append("--cgroup-manager=cgroupfs")
            cmd.append("--events-backend=none")
            cmd.extend(["-v", "/etc/localtime:/etc/localtime:ro"])
        elif self.runtime == "docker":
            cmd.extend(["-v", "/etc/localtime:/etc/localtime:ro"])

        # 3. Environment Variables
        for k, v in env.items():
            cmd.extend(["-e", f"{k}={v}"])

        # 4. Mounts
        for m in mounts:
            cmd.extend(["-v", m])

        # 5. Image & Command
        cmd.append(image)
        cmd.extend(command)

        print(f"[Runtime] Executing: {' '.join(cmd)}")
        
        # Async Execution
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate(input=input_data.encode() if input_data else None)
        
        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        }
