
from Acquire.Registry import Registry


def run(args):
    """Call this function to return information about a trusted service"""

    try:
        service_uid = args["service_uid"]
    except:
        service_uid = None

    try:
        service_url = args["service_url"]
    except:
        service_url = None

    registry = Registry()

    service = registry.get_service(service_uid=service_uid,
                                   service_url=service_url)

    return {"service_data": service.to_data()}
