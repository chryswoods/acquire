
from Acquire.Compute import Cluster


def run(args):
    """This function returns the UIDs of all pending jobs"""
    passphrase = str(args["passphrase"])

    cluster = Cluster.get_cluster()

    job_uids = cluster.get_pending_job_uids(passphrase=passphrase)

    return {"job_uids": cluster.encrypt_data(job_uids)}
