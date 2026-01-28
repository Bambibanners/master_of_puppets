# Installation Guide: Master of Puppets SRE Platform

This guide covers the installation of the Puppeteer Server (the Control Plane).
We offer two methods:
1.  **Automatic (Loader):** Recommended for appliances. Uses a "Matryoshka" container to bootstrap the stack.
2.  **Manual (Script):** Advanced. Runs directly on the host.

## Prerequisites
*   **OS:** Windows 10/11, Linux (Ubuntu/Debian/RHEL), or macOS.
*   **Runtime:** `podman` (v4.0+) installed and on PATH.

---

## Method 1: Automatic (Loader Container) 🚀

This method uses a specialized "Loader" container to handle dependencies, secrets, and configuration. It keeps your host clean.

### Steps
1.  **Clone or Download** the repository (or just get the installer script).
2.  Open a terminal in `puppeteer/`.
3.  Run the installer:
    *   **Windows (PowerShell):**
        ```powershell
        ./installer/install_universal.ps1 -Role Agent
        ```
    *   **Linux/Mac:**
        ```bash
        podman run --privileged --rm -it \
          -v /var/run/podman.sock:/run/podman/podman.sock \
          -v $PWD:/app \
          ghcr.io/bambibanners/puppeteer-loader:latest
        ```
        *(Note: Until the image is published, you must build it locally using `podman build -t puppeteer-loader -f loader/Containerfile .`)*

4.  Select **Option [1]**.
5.  Follow the prompts to enter your **DuckDNS Token** and **Domain**.
6.  The loader will invoke `podman-compose` via the socket and launch the stack.

### Verification
Visit `https://<your-domain>.duckdns.org`. You should see the Green Lock.

---

## Method 2: Manual (Script/host) 🛠️

Use this if you want full visibility into the process or need to debug `docker-compose` interactions.

### Prerequisites (Host)
*   **Python:** 3.12+
*   **Pip:** Installed.
*   **Podman-Compose:** `pip install podman-compose`
*   **OpenSSL:** On PATH (for key generation).

### Steps
1.  Open terminal in `puppeteer/`.
2.  Run the installer:
    ```powershell
    ./installer/install_universal.ps1 -Role Agent
    ```
3.  Select **Option [2]**.
4.  The script will:
    *   Check for `secrets.env`.
    *   Build the `cert-manager` image using your local tools.
    *   Run `podman-compose up`.

---

## Architecture Explained
The "Loader" pattern works by establishing a **Sibling** relationship.
The Loader container talks to your Host's Podman Socket. When it says "run database", it doesn't run inside the loader; it asks the Host to run it.
This ensures that when the Loader exits, your Server stays running!

## Troubleshooting

### "Socket Not Found" (Loader)
*   **Linux:** Ensure `-v /var/run/podman.sock:/run/podman/podman.sock` is passed.
*   **Windows:** Ensure you are running in a shell that can access the Podman Machine pipe, or use the PowerShell script which handles this (mostly). *Note: On pure Windows without WSL2/Podman Machine, socket mapping is complex.*

### "Green Lock Failed"
*   Check `podman logs puppeteer-cert-manager-1`.
*   Verify Port 80/443 are forwarded to your machine.
