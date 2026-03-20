class ResourceLimitsInterface:
    """CE stub: no resource limits, return None for all."""

    def get_node_limits(self, node_id: str):
        return None

    def get_job_limits(self, job_id: str):
        return None
