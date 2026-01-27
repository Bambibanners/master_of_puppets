# Handoff Instructions - Dashboard Fixes & Remote Deployment

## Current State
The local debugging session was successful. We resolved a "black screen" issue on the Dashboard and fixed API routing issues.

### ✅ What's Fixed (Locally)
1.  **Dashboard "Black Screen"**:
    *   **Cause**: `ReferenceError: Signatures is not defined` in `AppRoutes.tsx`.
    *   **Fix**: Restored missing imports in `AppRoutes.tsx`.
2.  **API Routing**:
    *   **Context**: Dashboard was hardcoded to `https://localhost:8001`, which fails in production/remote setups properly.
    *   **Fix**:
        *   Updated `auth.ts` and all Views (`Dashboard`, `Jobs`, etc.) to use **relative paths** (e.g., `/api/nodes`).
        *   Updated `cert-manager/Caddyfile` to proxy `/api/*` requests to the `agent` service.
3.  **Caching Issues**:
    *   **Cause**: Browser aggressively cached the broken JS bundle.
    *   **Fix**: Added `Cache-Control: no-store, no-cache` to the Nginx config in `dashboard/Containerfile`.

### 📌 Next Steps (For the Next Agent)
The codebase is now fixed and committed properly. The **IMMEDIATE** next step is to deploy these fixes to the remote `speedy_mini` node.

1.  **Deploy to Speedy Mini**:
    *   Run `python remote_deploy.py`.
    *   **Note**: This script handles the scp sync, cleanup, and sequential build process.
    *   **Important**: The remote build (`npm install`, etc.) takes time on the ARM64 Pi. Be patient.

2.  **Verify Remote**:
    *   Once deployed, check `https://master-of-puppets.duckdns.org` (or whatever the domain points to, or IP).
    *   Ensure the "System Login" screen appears (no black screen).
    *   Verify the "Green Lock" (SSL) is present.

### ⚠️ Watch Outs
*   **Browser Caching**: Even with the new headers, you might need to ask the user to Hard Refresh (`Ctrl+F5`) if they still see issues.
*   **Remote Resources**: `speedy_mini` is resource constrained. If `remote_deploy.py` fails, check for OOM. The sequential build strategy is already in place to mitigate this.
