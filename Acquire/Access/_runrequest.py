
from Acquire.Access import Request as _Request

__all__ = ["RunRequest"]


class RunRequest(_Request):
    """This class holds a request to run a particular calculation
       on a RunService. The result of this request will be a
       Location in which the output from this request can
       be read.
    """
    def __init__(self, image=None, input=None, resources=None):
        """Construct the request specifying the container image 'image'
           that contains the software used for the calculation,
           and the location of the input files 'input' that will be
           downloaded and run using this container.

           You can also optionally supply the compute resources
           (resources) that will be needed to run this job
        """
        super().__init__()

        self._uid = None
        self._image = str(image)
        self._resources = resources

        self._input = input

        if self._input is not None:
            from Acquire.Client import Location as _Location
            if not isinstance(self._input, _Location):
                raise TypeError("The input location must be type Location")

            from Acquire.ObjectStore import create_uid as _create_uid
            self._uid = _create_uid()

    def is_null(self):
        """Return whether or not this is a null request"""
        return self._uid is None

    def __str__(self):
        if self.is_null():
            return "RunRequest::null"
        else:
            return "RunRequest(uid=%s, image=%s, input=%s)" % (
                    self._uid, self._image, self._input)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def uid(self):
        """Return the UID of this request"""
        return self._uid

    def fingerprint(self):
        """Return a unique fingerprint for this request that can be
           used for signing and verifying authorisations
        """
        if self.is_null():
            return None

        return "%s|%s|%s" % (self.uid(), self.image(),
                             self.input().to_string())

    def image(self):
        """Return the full path to the container image used for the
           simulation
        """
        if self.is_null():
            return None
        else:
            return self._image

    def input(self):
        """Return the location of the input files used for this
           calculation
        """
        if self.is_null():
            return None
        else:
            return self._input

    def resources(self):
        """Return the resources requested to run this job"""
        if self.is_null():
            return None
        else:
            return self._resources

    def to_data(self):
        """Return this request as a json-serialisable dictionary"""
        if self.is_null():
            return {}

        data = super().to_data()
        data["uid"] = self._uid
        data["input"] = self._input.to_data()

        if self._image is not None:
            data["image"] = self._image

        if self._resources is not None:
            data["resources"] = str(self._resources)

        return data

    @staticmethod
    def from_data(data):
        """Creates a RunRequest object from the JSON data in data"""
        if data and len(data) > 0:
            from Acquire.Client import Location as _Location
            r = RunRequest()
            r._from_data(data)

            r._uid = data["uid"]
            r._input = _Location.from_data(data["input"])

            if "image" in data:
                r._image = str(data["image"])

            if "resources" in data:
                r._resources = str(data["resources"])

            return r

        return None
