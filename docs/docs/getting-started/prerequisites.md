# Prerequisites

Before installing Axiom, verify your environment meets the following requirements.

## Checklist

- [ ] **Docker 24+ with Docker Compose v2**

    verify with:
    ```bash
    docker --version && docker compose version
    ```

    You need Docker Engine 24.0 or later and the `docker compose` v2 plugin (note: not the legacy `docker-compose` v1 binary). Check that `docker compose version` outputs `v2.x.x` or higher.

- [ ] **4 GB RAM available**

    verify with:
    ```bash
    # Linux
    free -h
    ```

    On Mac, check **Activity Monitor → Memory**. On Windows, open **Task Manager → Performance → Memory**. Ensure at least 4 GB is free before starting the stack.

- [ ] **Ports 80 and 443 available**

    verify with:
    ```bash
    # Linux
    ss -tlnp | grep -E ':80|:443'

    # macOS
    netstat -an | grep LISTEN | grep -E ':80|:443'
    ```

    No output means the ports are free. If a service is already listening on 80 or 443, stop it before starting the stack (Caddy needs both ports).

- [ ] **Git** (to clone the repository)

    verify with:
    ```bash
    git --version
    ```

---

!!! tip "Podman Compose"
    The Axiom stack runs under Podman as a drop-in alternative to Docker. To verify your Podman installation:
    ```bash
    podman-compose --version
    ```
    Substitute `podman compose` for `docker compose` in all commands throughout this guide.

!!! info "Corporate / enterprise proxy"
    If deploying behind a corporate proxy, set the standard proxy environment variables before running `docker compose`:
    ```bash
    export HTTP_PROXY=http://proxy.example.com:8080
    export HTTPS_PROXY=http://proxy.example.com:8080
    export NO_PROXY=localhost,127.0.0.1
    ```

---

**Next:** [Install →](install.md)
