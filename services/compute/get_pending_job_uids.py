
from Acquire.Compute import Cluster


def run(_args):
    """This function returns the UIDs of all pending jobs"""
    cluster = Cluster.get_cluster()

    return {"job_uids": cluster.get_pending_job_uids()}
