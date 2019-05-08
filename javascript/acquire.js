/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

a0_a0_public_key = {'bytes': 'LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUE1UWZXdnVPVFROeEJ2ZkhZak5FcwpzU3czMUxxUWhlN211UExheXgwT3N1YjJTVUxlZCtXTkRScUxROHpJQTc3bG1hNXArTGpDTVFUZnoxaTlSSVBmCnI0SDBxa3YxMmYzYVNiVjN0aFFUekNIekoxMi9lNDJTVi8wZnhOejB1azhIbUsrSk9zOHg3dm5BUWxxbEJDVmIKM0hqQ0pwUy9IUGJXaXZxM1RjaFlJbkltWXdjaU8rdXZvZzZuTEJOSHhHOUZBTTRMWFprcnBXWmhJa2doOUhZOQpGUjhiZkJhNmdvQmpmM3QwUVlNUHBpaWd6K0NSU2JDQ2xCVzV6SW1iWGhnUHJsQVZKY2w2c2l0T0xRQVVIUHNUCnlvQzU0VmpvNVZVeFhqYkpEbXZzTERiQnUzZ0xWOVd0MGVvMHpBdGlmR3R0WXdmRndFSThOTi84MnBlUXJQZ0gKQlFJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=='};
a0_a0_public_certificate = {'bytes': 'LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUExVmhwOGtqY3VyUWtmWDU3Q2NKZApWbkNlblNxWllMRmJoVCt0SVVMa0lTdG9EWjVVWFRub241aUJOdFEzWkxDbG5RVTdxZEFjMzlLSlh1QmZ1M3RzCk1iaUE5YUpUQURPcEFPclBiRFhTcHI2Q0J4WkRzczF3NkxodlpISmRzNW50OUQzUnVaaTQ5ZXlZZ0oxVVR3aHQKMkJXM2hRcWVoMVkxY294QU9YSWtlZUpvZnFvOWMzaE4wQ21ZVE5kKzRlZ1Rmd2tLUHovNEZaYnlHUVg3dmF2aApoelBXSWw5U0xuTDBIdDBHMUVvN3hzd1VEMHVUbk80VGdmcmdHWmZaNVU5cjNFa2xrMTg0KzdFZGRGVXphSlgwClF1TjROd0ErbGN5ZHNFRW5oaXpIVjNoUS84U2k2ZjZFNlM5djJQTU44anpYdFhtRFZ2VzNENjJ5SFVndmdXUzkKNHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=='};
a0_a0_service_url = "http://fn.acquire-aaai.com:8080/t/registry";

var root_server = {"a0-a0":
                    {"service_url": a0_a0_service_url,
                     "public_key": a0_a0_public_key,
                     "public_certificate": a0_a0_public_certificate}};

/** Standardise the passed datetime into UTC */
function datetime_to_datetime(d)
{
    var date = new Date(d);
    var now_utc =  Date.UTC(date.getUTCFullYear(), date.getUTCMonth(),
                            date.getUTCDate(), date.getUTCHours(),
                            date.getUTCMinutes(), date.getUTCSeconds());

    return new Date(now_utc);
}

/** Convert the passed datetime into a standard formatted string */
function datetime_to_string(d)
{
    d = datetime_to_datetime(d);
    return d.toISOString();
}

/** Convert the passed string back into a datetime */
function string_to_datetime(s)
{
    return datetime_to_datetime(Date.parse(s));
}

/** Call the specified URL */
async function call_function({service_url=undefined, func=undefined,
                             args=undefined, args_key=undefined,
                             response_key=undefined, public_cert=undefined})
{
    var response = null;
    var body = {};

    if (body == {})
    {
        body = undefined;
    }
    else
    {
        body = JSON.stringify(body);
    }

    body = undefined;

    response = fetch(service_url,
               {
                    method: 'post',
                    headers: {
                        'Accept': 'application/json, test/plain, */*',
                        'Content-Type': 'application/json'
                    },
                    body: body
                })
                .then(response => response.json());

    try
    {
        response = await response;
    }
    catch(err)
    {
        console.log(`ERROR CALLING FUNCTION ${service_url} ${body}`);
        console.log(`ERROR == ${err}`);
        return undefined;
    }

    try
    {
        response = JSON.parse(response);
        payload = response.payload;
    }
    catch(err)
    {
        console.log(`ERROR CALLING FUNCTION ${service_url} ${body}`);
        console.log(`ERROR EXTRACTING JSON ${response}`);
        console.log(`ERRRO = ${err}`);
        return undefined;
    }

    if (payload["status"] == -1)
    {
        console.log(`ERROR IN PAYLOAD ${payload}`);
        return undefined;
    }

    return payload.return;
}

class PublicKey
{
    constructor()
    {

    }

    to_data()
    {
        data = {};
        return data;
    }

    static from_data(data)
    {
        var key = new PublicKey();
        return key;
    }
}

class Service
{
    /** Construct a service that is accessed at 'service_url'.
     *  This will automatically connect to the service to obtain
     *  the necessary service information.
     *
     *  Args:
     *      service_url = URL of the service to connect to
     *      service_uid = UID of the service to connect to
     *      service_type = expected type of the service
     */
    constructor({service_url=undefined, service_uid=undefined,
                 service_type=undefined} = {})
    {
        this._canonical_url = service_url;
        this._uid = service_uid;
        this._service_type = service_type;
    }

    /** Return whether or not this is a null Service */
    is_null()
    {
        return this._uid == undefined;
    }

    /** Return the UID of this service */
    uid()
    {
        return this._uid;
    }

    /** Return the type of this Service */
    service_type()
    {
        if (this.is_null()){ return undefined; }
        else { return this._service_type; }
    }

    /** Return the UID of the registry that registered this service */
    registry_uid()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            var root = this.uid().split("-")[0];
            return `${root}-${root}`;
        }
    }

    to_data()
    {
        var data = {};

        if (this.is_null()){ return data; }

        data["uid"] = this._uid;
        data["service_type"] = this._service_type;
        data["canonical_url"] = this._canonical_url;
        data["domain"] = this._domain;
        data["ports"] = this._ports;
        data["schemes"] = this._schemes;
        data["path"] = this._path;

        data["service_user_uid"] = this._service_user_uid;
        data["service_user_name"] = this._service_user_name;

        try
        {
            data["public_key"] = this._pubkey.to_data();
        }
        catch
        {
            data["public_key"] = undefined;
        }

        try
        {
            data["public_certificate"] = this._pubcert.to_data();
        }
        catch
        {
            data["public_certificate"] = undefined;
        }

        data["last_key_update"] = datetime_to_string(this._last_key_update);
        data["key_update_interval"] = this._key_update_interval;

        return data;
    }

    static from_data(data)
    {
        var service = new Service();

        service._uid = data["uid"];
        service._service_type = data["service_type"];
        service._canonical_url = data["canonical_url"];
        service._domain = data["domain"];
        service._ports = data["ports"];
        service._schemes = data["schemes"];
        service._path = data["path"];

        service._service_user_uid = data["service_user_uid"];
        service._service_user_name = data["service_user_name"];

        service._pubkey = PublicKey.from_data(data["public_key"])
        service._pubcert = PublicKey.from_data(data["public_certificate"])

        service._last_key_update = string_to_datetime(data["last_key_update"])
        service._key_update_interval = parseFloat(data["key_update_interval"])

        return service;
    }
 }


async function test_acquire()
{
    service_url = root_server["a0-a0"]["service_url"];
    console.log(service_url);

    var response = await call_function({service_url: service_url});

    console.log(response);

    var s = Service.from_data(response["service_info"]);
    console.log(s);
    data = s.to_data();
    console.log(data);
    console.log(s.registry_uid());
    var s2 = Service.from_data(data);
    console.log(s2);
}
