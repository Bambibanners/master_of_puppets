# Speedy Mini Deployment Constraints

## Hardware Specifications
- **Hostname**: `speedy-mini` (192.168.50.128)
- **Platform**: Raspberry Pi 4 (ARM64 - Cortex-A72)
- **CPU**: 4 cores @ 56% scaling
- **RAM**: 1.8 GB total (effectively ~1.1 GB available after OS overhead)
- **Swap**: 2.0 GB
- **Storage**: 29 GB SD card (13 GB used, 15 GB available)
- **OS**: Ubuntu 24.04 LTS (Linux 6.17.0-1003-raspi)

## Critical Deployment Constraints

### Memory Management
⚠️ **CRITICAL**: This node has **severe memory constraints** (~1.8 GB RAM).

**Rules for Remote Deployment:**
1. **Never run more than 2 concurrent image builds** - Building the dashboard, server, and cert-manager simultaneously will cause OOM.
2. **Always use `--build` flag sparingly** - Prefer cached images when possible.
3. **Monitor swap usage** - If swap exceeds 500 MB, the node is thrashing.
4. **Use aggressive cleanup between deployments**:
   ```bash
   podman system prune -a -f --volumes
   ```

### Build Strategy for `speedy_mini`
When deploying to this node, use a **sequential build approach**:

```python
# In remote_deploy.py or similar scripts
# Build images ONE AT A TIME, not all at once via compose --build
commands = [
    "podman build -t localhost/app_cert-manager:v3 -f cert-manager/Containerfile cert-manager",
    "podman system prune -f",  # Clean between builds
    "podman build -t localhost/master-of-puppets-server:v3 -f Containerfile.server .",
    "podman system prune -f",
    "podman build -t localhost/master-of-puppets-dashboard:v3 -f dashboard/Containerfile dashboard",
    "podman system prune -f",
    # THEN launch with compose (no --build flag)
    "podman-compose -f compose.server.yaml up -d"
]
```

### NPM Build Constraints (Dashboard)
The dashboard build is particularly memory-intensive. **Always use**:
- `npm config set maxsockets 1`
- `--network-timeout=1000000`
- `--no-audit --no-fund`
- Consider using `registry.npmmirror.com` for faster downloads

### SSH Behavior
- **Expect hangs** when the node is under memory pressure
- **Always set reasonable timeouts** (30-60s max)
- **Use background commands** with status polling instead of blocking calls

### Image Tag Strategy
- **Use versioned tags** (e.g., `:v3`, `:v4`) instead of `:latest` to force cache invalidation
- **Increment version tags** when you need to ensure a fresh build

## Deployment Checklist
Before deploying to `speedy_mini`:
- [ ] Verify available memory: `free -h` (should have >800 MB available)
- [ ] Clean Podman cache: `podman system prune -a -f --volumes`
- [ ] Use sequential builds (not parallel)
- [ ] Monitor deployment logs for OOM killer messages
- [ ] If deployment hangs, assume OOM and perform manual cleanup

## Recovery Procedure
If the node becomes unresponsive:
1. User must manually SSH and run: `podman rm -f $(podman ps -aq); podman system prune -a -f --volumes`
2. Wait 2-3 minutes for cleanup to complete
3. Verify with `free -h` and `podman ps -a`
4. Only then retry deployment

---
*Last Updated: 2026-01-27*
*Node Owner: speedy@192.168.50.128*
