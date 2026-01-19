# Script Compatibility Contract

## Overview
When writing Python scripts to be executed by **Master of Puppets** Nodes, you must adhere to specific path and environment conventions to ensure cross-platform compatibility (Windows Host -> Linux Node).

## 1. Path Handling
Nodes run as **Linux Containers**. Windows paths (e.g., `C:\Data`) do not exist natively. However, the system provides **Managed Network Mounts** to bridge this gap.

### Best Practices
*   **Do NOT hardcode paths** like `C:\`.
*   **Use Environment Variables**: The Agent injects mapped paths as environment variables.

### Global Mounts
If you configure a Global Mount named `projects` pointing to `\\server\share`:
*   **Agent Injection**: `MOUNT_PROJECTS=/mnt/mop/projects`
*   **Python Usage**:
    ```python
    import os
    
    # CORRECT
    base_path = os.environ.get("MOUNT_PROJECTS")
    file_path = os.path.join(base_path, "data.csv")
    
    # INCORRECT
    file_path = "C:\\server\\share\\data.csv"
    ```

## 2. Environment Variables
The following variables are always available to your scripts:
*   `NODE_ID`: Unique ID of the executing node.
*   `JOB_ID`: ID of the current job.
*   `MOUNT_*`: Paths to configured network shares.

## 3. Libraries
The Node environment includes standard Python 3.12 libraries. 
*   **Standard Lib**: `os`, `sys`, `json`, `math`, etc.
*   **External Libs**: Not currently supported in dynamic scripts. Scripts must be self-contained or rely on pre-installed packages in the Node image.
