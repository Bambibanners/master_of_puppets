import time

def ping():
    print(f"[PING] Pong! Time: {time.time()}")
    return "Pong"

if __name__ == "__main__":
    ping()
