
import os

from Acquire.Service import login_to_service_account
from Acquire.Service import create_return_value
from admin.admin_user import login_admin_user


def run(args):
    status = 0
    message = "TEST"

    user = login_admin_user()

    return_value = create_return_value(status, message)
    return_value["admin_user"] = str(user)

    return return_value
