
from Acquire.Client import Identifier
from Acquire.ObjectStore import create_uid, get_datetime_now_to_string


def test_identifier():
    service_uid = "z0-z0"
    drive_guid = "%s@%s" % (create_uid(), service_uid)
    filename = "random å∫ç filename/some∑∑∑.txt"
    version = "%s/%s" % (get_datetime_now_to_string(),
                         create_uid(short_uid=True))

    drive_id = Identifier(drive_guid=drive_guid)

    assert(drive_id.is_drive())
    assert(not drive_id.is_file())
    assert(not drive_id.specifies_version())
    assert(drive_id.drive_guid() == drive_guid)
    assert(drive_id.service_uid() == service_uid)

    s = drive_id.to_string()
    drive_id2 = Identifier.from_string(s)

    assert(drive_id2.is_drive())
    assert(not drive_id2.is_file())
    assert(not drive_id2.specifies_version())
    assert(drive_id2.drive_guid() == drive_guid)
    assert(drive_id2.service_uid() == service_uid)

    data = drive_id.to_data()
    drive_id2 = Identifier.from_data(data)

    assert(drive_id2.is_drive())
    assert(not drive_id2.is_file())
    assert(not drive_id2.specifies_version())
    assert(drive_id2.drive_guid() == drive_guid)
    assert(drive_id2.service_uid() == service_uid)

    file_id = Identifier(drive_guid=drive_guid, filename=filename)

    assert(not file_id.is_drive())
    assert(file_id.is_file())
    assert(not file_id.specifies_version())
    assert(file_id.drive_guid() == drive_guid)
    assert(file_id.service_uid() == service_uid)
    assert(file_id.filename() == filename)

    s = file_id.to_string()
    file_id2 = Identifier.from_string(s)

    assert(not file_id2.is_drive())
    assert(file_id2.is_file())
    assert(not file_id2.specifies_version())
    assert(file_id2.drive_guid() == drive_guid)
    assert(file_id2.service_uid() == service_uid)
    assert(file_id2.filename() == filename)

    data = file_id.to_data()
    file_id2 = Identifier.from_data(data)

    assert(not file_id2.is_drive())
    assert(file_id2.is_file())
    assert(not file_id2.specifies_version())
    assert(file_id2.drive_guid() == drive_guid)
    assert(file_id2.service_uid() == service_uid)
    assert(file_id2.filename() == filename)

    file_id = Identifier(drive_guid=drive_guid, filename=filename,
                         version=version)

    assert(not file_id.is_drive())
    assert(file_id.is_file())
    assert(file_id.specifies_version())
    assert(file_id.drive_guid() == drive_guid)
    assert(file_id.service_uid() == service_uid)
    assert(file_id.filename() == filename)
    assert(file_id.version() == version)

    s = file_id.to_string()
    file_id2 = Identifier.from_string(s)

    assert(not file_id2.is_drive())
    assert(file_id2.is_file())
    assert(file_id2.specifies_version())
    assert(file_id2.drive_guid() == drive_guid)
    assert(file_id2.service_uid() == service_uid)
    assert(file_id2.filename() == filename)
    assert(file_id2.version() == version)

    data = file_id.to_data()
    file_id2 = Identifier.from_data(data)

    assert(not file_id2.is_drive())
    assert(file_id2.is_file())
    assert(file_id2.specifies_version())
    assert(file_id2.drive_guid() == drive_guid)
    assert(file_id2.service_uid() == service_uid)
    assert(file_id2.filename() == filename)
    assert(file_id2.version() == version)
