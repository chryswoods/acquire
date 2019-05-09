

class RemoteFunctionCallError
{
    constructor(error)
    {
        this.message = error;
    }
}

async function unpack_arguments({args=undefined, key=undefined,
                                 public_cert=undefined,
                                 is_return_value=false,
                                 func=undefined, service=undefined})
{
    var data = await args;

    if (data == undefined)
    {
        data = {};
    }

    var payload = undefined;

    if ("payload" in data)
    {
        payload = data["payload"];

        if ("error" in payload)
        {
            throw new RemoteFunctionCallError(payload["error"]);
        }

        if ("status" in payload)
        {
            if (payload["status"] != 0)
            {
                var err = JSON.stringify(payload);
                throw new RemoteFunctionCallError(err);
            }
        }
    }

    var is_encrypted = ("encrypted" in data);
    var signature = undefined;

    if (public_cert != undefined)
    {
        if (!is_encrypted)
        {
            throw new RemoteFunctionCallError(
                "Cannot unpack result as should be signed, but isn't. " +
                "Only encrypted results can be signed");
        }

        signature = data["signature"];

        if (signature == undefined)
        {
            throw new RemoteFunctionCallError(
                "We requested the data was signed, but no signature found!");
        }
    }

    if (is_encrypted)
    {
        var encrypted_data = string_to_bytes(data["data"]);
        var fingerprint = data["fingerprint"];

        var my_fingerprint = await key.fingerprint();

        if (fingerprint != my_fingerprint)
        {
            throw new RemoteFunctionCallError(
                "Cannot decrypt result - conflicting fingerprints " +
                `${fingerprint} versus ${my_fingerprint}`);
        }

        decrypted_data = await key.decrypt(encrypted_data);
        decrypted_data = JSON.parse(decrypted_data);

        return await unpack_arguments({args:decrypted_data,
                                       is_return_value:is_return_value,
                                       func:func, service:service});
    }

    if (payload == undefined)
    {
        throw new RemoteFunctionCallError(
            "Strange - no payload by this point in the call?");
    }

    return payload["return"];
}

async function unpack_return_value({return_value=undefined,
                                    key=undefined, public_cert=undefined,
                                    func=undefined, service=undefined})
{
    return await unpack_arguments({args:return_value,
                                   key:key, public_cert:public_cert,
                                   is_return_value:true,
                                   func:func, service:service});
}

async function pack_return_value({func=undefined, payload=undefined,
                                  key=undefined, response_key=undefined,
                                  public_cert=undefined,
                                  private_cert=undefined})
{
    if (func == undefined)
    {
        func = payload["function"];
    }

    result = {};

    var now = get_datetime_now_to_string();

    result["function"] = func;
    result["payload"] = payload;
    result["synctime"] = now;

    if (response_key != undefined)
    {
        var bytes = await response_key.bytes();
        bytes = string_to_utf8_bytes(bytes);
        bytes = bytes_to_string(bytes);
        result["encryption_public_key"] = bytes;

        if (public_cert != undefined)
        {
            var fingerprint = await public_cert.fingerprint();
            result["sign_with_service_key"] = fingerprint;
        }
    }

    var result_json = JSON.stringify(result);

    if (key != undefined)
    {
        // encrypt what we send to the server
        result_data = await key.encrypt(result_json);
        var fingerprint = await key.fingerprint();

        result = {};
        result["data"] = bytes_to_string(result_data);
        result["encrypted"] = true;
        result["fingerprint"] = fingerprint;
        result["synctime"] = now;
        result_json = JSON.stringify(result);
    }

    return result_json;
}

async function pack_arguments({func=undefined, args=undefined,
                               key=undefined, response_key=undefined,
                               public_cert=undefined})
{
    return await pack_return_value({func:func, payload:args,
                                    key:key, response_key:response_key,
                                    public_cert:public_cert});
}

/** Call the specified URL */
async function call_function({service_url=undefined, func=undefined,
                              args=undefined, args_key=undefined,
                              response_key=undefined, public_cert=undefined})
{
    if (args == undefined)
    {
        args = {};
    }

    var args_json = undefined;

    if (response_key == undefined)
    {
        args_json = await pack_arguments({func:func, args:args, key:args_key});
    }
    else
    {
        var pubkey = await response_key.public_key();
        args_json = await pack_arguments({func:func, args:args, key:args_key,
                                          response_key:pubkey,
                                          public_cert:public_cert});
    }

    var response = null;

    response = fetch(service_url,
    {
        method: 'post',
        headers: {
            'Accept': 'application/json, test/plain, */*',
            'Content-Type': 'application/json'
            },
        body: args_json
    })
    .then(response => response.json());

    try
    {
        response = await response;
    }
    catch(err)
    {
        throw new RemoteFunctionCallError(
            `Error calling function ${service_url} ` +
            `Error = ${err}`);
    }

    var result = undefined;

    try
    {
        result = JSON.parse(response);
    }
    catch(err)
    {
        throw new RemoteFunctionCallError(
            `Error extracting json from function ${service_url} ` +
            `json = ${args_json}, Error = ${err}`);
    }

    result = await unpack_return_value({return_value:result, key:response_key,
                                        public_cert:public_cert, func:func,
                                        service:service_url});

    return result;
}
