
__all__ = ["JobSheet"]


class JobSheet:
    """This class holds a complete record of a job that the access
       service has been asked to perform.
    """
    def __init__(self, job=None):
        if job is not None:
            from Acquire.ObjectStore import create_uuid as _create_uuid
            self._job = job
            self._uid = _create_uuid()
        else:
            self._uid = None

    def set_storage_service(self, service, quoted_cost):
        """Set the storage service to be used for uploading the
           input and saving the output
           from the job, together with the quoted cost. Note
           that you cannot set a new storage service once
           the payment for the job has been received
        """
        pass

    def add_compute_service(self, service, quoted_cost):
        """Set the compute service to be used for actually performing
           the job. Note that you cannot set a new compute service
           once the payment for the job has been received
        """
        pass

    def total_cost(self):
        """Return the total maximum quoted cost for this job. The
           total cost to run the job must not exceed this
        """
        pass

    def add_credit_notes(self, credit_notes):
        """Add the credit notes that contain the source of value of
           paying for this job. This will check whether or not
           the
        """
        pass

    def add_debit_notes(self, service, debit_notes):
        """Add the debit notes recording the payment for the
           work on 'service' from our account
        """
        pass

    def set_output_par(self, par):
        """Set a secure record of the write-par used to write the
           output from the job to the storage service. Note that this
           DOES NOT store the PAR itself - just a record of the PAR
        """
        pass

    def set_input_par(self, par):
        """Set a secure record of the """