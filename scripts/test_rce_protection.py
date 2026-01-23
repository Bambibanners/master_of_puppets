import asyncio
import os
import shutil
from environment_service.node import Node

async def test_rce_fail_closed():
    print("--- Testing RCE Fail-Closed ---")
    
    # 1. Setup Mock Node
    # Monkeypatch init methods to avoid network calls
    Node.ensure_identity = lambda self: print("Mocking Identity")
    Node.bootstrap_trust = lambda self: print("Mocking Trust")
    
    node = Node("http://localhost:8001", "test-node")
    node.verify_key_path = "secrets/missing_key.pem" # Point to non-existent key
    
    # Ensure key doesn't exist
    if os.path.exists(node.verify_key_path):
        os.remove(node.verify_key_path)
        
    # 2. Construct Job with Signature
    job = {
        "guid": "test-job-1",
        "task_type": "python_script",
        "payload": {
            "script_content": "print('PWNED')",
            "signature": "c29tZWFrZXNpZ25hdHVyZQ==" # Dummy base64 signature
        }
    }
    
    # 3. patch report_result to capture output instead of hitting network
    results = []
    async def mock_report(guid, success, result):
        results.append((success, result))
        print(f"Reported: Success={success}, Result={result}")

    node.report_result = mock_report
    
    # 4. Execute
    await node.execute_task(job)
    
    # 5. Assertions
    if len(results) == 1:
        success, result = results[0]
        if success is False and "Security Check Failed: Verification Key missing" in result.get("error", ""):
            print("✅ check passed: Node refused to execute script without key.")
        else:
            print(f"❌ check failed: Node did not fail as expected. {result}")
    else:
        print("❌ check failed: No result reported.")

async def test_missing_signature():
    print("--- Testing Missing Signature ---")
    
    Node.ensure_identity = lambda self: print("Mocking Identity")
    Node.bootstrap_trust = lambda self: print("Mocking Trust")
    node = Node("http://localhost:8001", "test-node")
    
    # Job without signature
    job = {
        "guid": "test-job-unsigned",
        "task_type": "python_script",
        "payload": {
            "script_content": "print('BAD')",
            # "signature" is missing
        }
    }
    
    results = []
    async def mock_report(guid, success, result):
        results.append((success, result))
        print(f"Reported: Success={success}, Result={result}")
    node.report_result = mock_report
    
    await node.execute_task(job)
    
    if len(results) == 1:
        success, result = results[0]
        if success is False and "Signature Missing (Mandatory)" in result.get("error", ""):
            print("✅ check passed: Node refused to execute unsigned script.")
        else:
             print(f"❌ check failed: Node did not fail as expected. {result}")
    else:
         print("❌ check failed: No result reported.")

if __name__ == "__main__":
    try:
        asyncio.run(test_rce_fail_closed())
        asyncio.run(test_missing_signature())
    except Exception as e:
        print(f"Test crashed: {e}")
