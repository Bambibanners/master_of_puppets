# Job Scheduling

v1.2 introduces native support for recurring tasks using standard Cron expressions.

## Creating a Scheduled Job

Scheduled Jobs are defined once and execute repeatedly.

### 1. Components
*   **Name**: Unique identifier.
*   **Script**: The Python code to execute.
*   **Schedule**: A standard 5-part Cron expression (`* * * * *`).
*   **Signature**: A valid Ed25519 signature of the script.

### 2. Cron Syntax
Supported fields:
*   Minute (0-59)
*   Hour (0-23)
*   Day of Month (1-31)
*   Month (1-12)
*   Day of Week (0-6)

**Examples**:
*   `*/5 * * * *` : Every 5 minutes.
*   `0 8 * * *` : Every day at 8:00 AM.
*   `0 0 * * 0` : Every Sunday at Midnight.

## API Usage

See [Deployment Guide](../deployment_guide.md) for automated creation of Scheduled Jobs.

## execution History

The Dashboard provides a Sparkline visualization for the last 30 executions of each job, allowing quick identification of failure patterns.
