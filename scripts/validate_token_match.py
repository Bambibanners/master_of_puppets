import json
import base64

# Token from diagnostic output (Step 828)
REMOTE_TOKEN_B64 = "eyJ0IjogImFjNDIzMDQ0NDcyMjQ3N2JhMTYyZTViZTk1OWYzODk4IiwgImNhIjogIi0tLS0tQkVHSU4gQ0VSVElGSUNBVEUtLS0tLVxuTUlJRmJUQ0NBMVdnQXdJQkFnSVVEd0VZZU94M1A4blF0WEtuaWMzZU5tVkw3MlV3RFFZSktvWklodmNOQVFFTFxuQlFBd1pqRUxNQWtHQTFVRUJoTUNWVk14RXpBUkJnTlZCQWdNQ2tONVltVnljM0JoWTJVeElqQWdCZ05WQkFvTVxuR1ZCMWNIQmxkQ0JOWVhOMFpYSWdTVzUwWlhKdVlXd2dRMEV4SGpBY0JnTlZCQU1NRlZCMWNIQmxkQ0JOWVhOMFxuWlhJZ1VtOXZkQ0JEUVRBZUZ3MHlOakF4TWpJeE9UUTJNalphRncwek5qQXhNakF4T1RRMk1qWmFNR1l4Q3pBSlxuQmdOVkJBWVRBbFZUTVJNd0VRWURWUVFJREFwRGVXSmxjbk53WVdObE1TSXdJQVlEVlFRS0RCbFFkWEJ3WlhRZ1xuVFdGemRHVnlJRWx1ZEdWeWJtRnNJRU5CTVI0d0hBWURWUVFEREJWUWRYQndaWFFnVFdGemRHVnlJRkp2YjNRZ1xuUTBFd2dnSWlNQTBHQ1NxR1NJYjNEUUVCQVFVQUE0SUNEd0F3Z2dJS0FvSUNBUUNuSzBDSFRrbXZQS1hJSEovelxudVNXSEZ3a2s3bnVDTzhuNUxjYWg3QWpNWDBHcHViQWhaWXEyQjlQSmRvblVsOW1ubkJPdndlUjNvWlhhTTZ1L1xuVnpEM05NN0lNRWxvNVJDUWsvVDlzYzRMd0s4bEJ5M0lZWStZUXhXVXpPYm9JT0ZFTXBmL0J3RGpNSDNRZEdzaVxuWjN1ZFk5NkMxZGNUSEJPckFrL2tNUFJNUXlUVEhNUElDTGFKc0d1V0R6QlNBNHRMMkpyMzNYQzNyaDlEUTdXMFxuMi9VbWsrWDhIYnl3aGsyaGswaFFTc2swRVpqZ0I1S1BOS0E1RnAwcHpua1pWenJFOXpRZ2w0bStDSklKbVh4eVxuU2FpYXpiUC9FWFQ1eXZTcWtIN2dpNHlRcXJkZmJmY1Axd2lMMURGaUVBMUx2Vjl4eWV6dE12Y3dFbmZqUFh4MFxuWjdtM0ZvMUd3b0FNSDB3NEdsUzg5WWRGR254RUlnb3prZnB0QkxXeTNnNGZyRFVOZE1CYTlSTnY2OXVKNlBCclxubDl4MTIwT3pnbjdyWVZ6ZEVLWG4rcVVVOGNPWU5ta0hHOWFFSnlRcEZxK2wxY1VkalV6N1ZnR2UrRkRJRW1SU1xuVkhQT2pKbStRNExwdldMOTZrQXg3S3ZSYXhreTl0OUZSejVRM2VQb1oxUEwrbTMrTTVKVExKK3c2ZlFKRHB1T1xuL1RHN2tRSWRZbkFMUDJGSDhsRDBzV29wNzFudVAxRm8vbEVjL0wwajZLeHd0MjJnaysrTXJOUS9MbDBUK2JNd1xudWpqS2FUMVY1N0tweGdSbFlRZEZmRHM5ajFNNlkvLzZMbU5OS2tBdWIrLzJLK3NULzJYbVNROVl1NTkvSlN4VlxuVFg3cktIbVFRWUh5Yi9qQ0JEbDh2NFExVndJREFRQUJveE13RVRBUEJnTlZIUk1CQWY4RUJUQURBUUgvTUEwR1xuQ1NxR1NJYjNEUUVCQ3dVQUE0SUNBUUJ2TThrQlZmbitLTWNKMkdBTHptZDl0MU1vR1V5TlVlUm5wVHpaMFFoRVxuTEJENzE3UzB2VWJUSU9ncnMrdGlOYnVDK2h6OERJR0cvTSsvZmRpbTEwSXVaZ3FvQW9yTndkNkxwS1NKcDk2UVxuNkdjVGthVXdzMFhYb01UaHZyVmpxYTR0YnNyUGRHTHNRTlRPeU93S3orbGMvWlQ3TmZ3YnVSek44c1E3cktvalxuVEZvMjF2"

def validate():
    # 1. Decode Remote Token
    try:
        remote_json = base64.b64decode(REMOTE_TOKEN_B64).decode()
        remote_payload = json.loads(remote_json)
        remote_ca = remote_payload.get("ca", "").strip()
        print(f"Remote Token Decoded OK.")
    except Exception as e:
        print(f"Failed to decode remote token: {e}")
        return

    # 2. Read Local CA
    with open("secrets/ca/root_ca.crt", "r") as f:
        local_ca = f.read().strip()
        
    # 3. Compare content
    if remote_ca == local_ca:
        print("SUCCESS: Remote Token CA matches Local CA.")
    else:
        print("FAILURE: Remote Token CA does NOT match Local CA.")
        print(f"Remote length: {len(remote_ca)}")
        print(f"Local length: {len(local_ca)}")
        
        # Compare first few chars
        print(f"Remote start: {remote_ca[:50]}...")
        print(f"Local start: {local_ca[:50]}...")

        # Find first diff
        for i in range(min(len(remote_ca), len(local_ca))):
            if remote_ca[i] != local_ca[i]:
                print(f"Mismatch at index {i}: Remote '{remote_ca[i]}' vs Local '{local_ca[i]}'")
                break

if __name__ == "__main__":
    validate()
