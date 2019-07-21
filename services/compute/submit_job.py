
from Acquire.Client import PAR, Cheque, Drive
from Acquire.Access import RunRequest
from Acquire.Service import get_this_service
from Acquire.Compute import ComputeJob


def run(args):
    """This function receives the request to submit a job on the
       compute service. It processes the request and performs
       everything needed to actually submit the job. This
       returns confirmation the job has been submitted, as
       well as some metadata about the job
    """
    worksheet_uid = str(args["worksheet_uid"])
    request = RunRequest.from_data(args["request"])
    par = PAR.from_data(args["par"])
    secret = args["secret"]
    cheque = Cheque.from_data(args["cheque"])

    job = ComputeJob.submit(worksheet_uid=worksheet_uid,
                            request=request, par=par,
                            secret=secret, cheque=cheque)

    return {"uid": job.uid()}
