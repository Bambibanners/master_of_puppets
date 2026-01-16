import asyncio
import httpx
import uuid
import os
import json
from typing import Optional, Dict

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8001")
NODE_ID = f"node-{uuid.uuid4().hex[:8]}"

class Node:
    def __init__(self, agent_url: str, node_id: str):
        self.agent_url = agent_url
        self.node_id = node_id
        self.running = False

    async def poll_for_work(self) -> Optional[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.agent_url}/work/pull")
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return data # {"guid": "...", "payload": {...}}
        except Exception as e:
            print(f"[{self.node_id}] Error polling Agent: {e}")
        return None

    async def execute_task(self, job: Dict):
        guid = job["guid"]
        payload = job["payload"]
        print(f"[{self.node_id}] Executing Job {guid} - Payload: {payload}")
        
        # Simulate work
        await asyncio.sleep(2)
        
        # Result
        success = True
        result_data = {"processed": True, "details": "Task complete"}
        
        await self.report_result(guid, success, result_data)

    async def report_result(self, guid: str, success: bool, result: Dict):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.agent_url}/work/{guid}/result",
                    json={"success": success, "result": result}
                )
            print(f"[{self.node_id}] Reported result for {guid}")
        except Exception as e:
            print(f"[{self.node_id}] Failed to report result: {e}")

    async def start(self):
        print(f"[{self.node_id}] Starting Node Loop...")
        self.running = True
        while self.running:
            job = await self.poll_for_work()
            if job:
                await self.execute_task(job)
            else:
                # Backoff
                await asyncio.sleep(5)

if __name__ == "__main__":
    node = Node(AGENT_URL, NODE_ID)
    try:
        asyncio.run(node.start())
    except KeyboardInterrupt:
        print("Node stopping...")
