
from Acquire.Client import Authorisation
from Acquire.Compute import Cluster


def run(args):
    """Admin function used to set the cluster that will be used to
       actually perform jobs
    """

    authorisation = Authorisation.from_data(args["authorisation"])
    cluster = Cluster.from_data(args["cluster"])

    Cluster.set_cluster(cluster=cluster, authorisation=authorisation)

    return {"cluster": cluster.to_data()}
