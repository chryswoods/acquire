
__all__ = ["Resources"]


class Resources:
    """This class holds the full set of requestable resources needed
       for a Job submitted to the system. This includes the
       container URL for any container images used by the job,
       the number of nodes and processors, the amount of memory per node,
       the amount of disk space needed etc.
    """
    def __init__(self, image=None, nodes=1, cores_per_node=1,
                 mem_per_core="100MB", gpus_per_node=0, shape=None,
                 tmp_disk_per_node="4GB", scratch_disk="10GB",
                 campaign_disk="5GB"):
        """Construct a set of resources specifying everything that may
           be needed to obtain sufficient resource to run a job
        """
        self._image = str(image)
        self._nodes = int(nodes)
        self._cores_per_node = int(cores_per_node)
        self._mem_per_core = str(mem_per_core)
        self._gpus_per_node = int(gpus_per_node)

        if shape is not None:
            self._shape = str(shape)
        else:
            self._shape = None

        self._tmp_disk_per_node = str(tmp_disk_per_node)
        self._scratch_disk = str(scratch_disk)
        self._campaign_disk = str(campaign_disk)

    def to_data(self):
        """Return a json-serialisable dictionary of this data"""
        data = {}

        data["image"] = self._image
        data["nodes"] = self._nodes
        data["cores_per_node"] = self._cores_per_node
        data["mem_per_core"] = self._mem_per_core
        data["gpus_per_node"] = self._gpus_per_node
        data["shape"] = self._shape
        data["tmp_disk_per_node"] = self._tmp_disk_per_node
        data["scratch_disk"] = self._scratch_disk
        data["campaign_disk"] = self._campaign_disk

        return data

    @staticmethod
    def from_data(data):
        """Return Resources constructed from a json-deserialised dictionary"""
        r = Resources()

        if data is None or len(data) == 0:
            return r

        r.image = str(data["image"])
        r._nodes = int(data["nodes"])
        r._cores_per_node = int(data["cores_per_node"])
        r._mem_per_core = str(data["mem_per_core"])
        r._gpus_per_node = str(data["gpus_per_node"])
        r._shape = str(data["shape"])
        r._tmp_disk_per_node = str(data["tmp_disk_per_node"])
        r._scratch_disk = str(data["scratch_disk"])
        r._campaign_disk = str(data["campaign_disk"])

        return r
