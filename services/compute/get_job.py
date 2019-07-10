
from Acquire.Compute import Cluster


def run(args):
    """This function gets the job with the specified UID in the specified
       state, optionally changing it to a new state
    """

    uid = str(args["uid"])
    passphrase = str(args["passphrase"])
    start_state = str(args["start_state"])

    try:
        end_state = str(args["end_state"])
    except:
        end_state = None

    cluster = Cluster.get_cluster()

    job = cluster.get_job(uid=uid, passphrase=passphrase,
                          start_state=start_state, end_state=end_state)

    return {"job": cluster.encrypt_data(job.to_data())}
