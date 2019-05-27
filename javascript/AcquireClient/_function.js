
Acquire.unpack_arguments = async function(
                                {args=undefined, key=undefined,
                                 public_cert=undefined,
                                 is_return_value=false,
                                 func=undefined, service=undefined})
{
    let data = await args;

    if (data == undefined)
    {
        data = {};
    }

    let payload = undefined;

    if ("payload" in data)
    {
        payload = data["payload"];

        if ("exception" in payload)
        {
            throw new Acquire.RemoteFunctionCallError(
                "Error calling remote function", payload["exception"]);
        }
        else if ("error" in payload)
        {
            throw new Acquire.RemoteFunctionCallError(
                    "Error calling remote function", payload["error"]);
        }
        else if ("status" in payload)
        {
            if (payload["status"] != 0)
            {
                throw new Acquire.RemoteFunctionCallError(
                    "Error calling remote function", payload);
            }
        }
    }

    let is_encrypted = ("encrypted" in data);
    let signature = undefined;

    if (public_cert != undefined)
    {
        if (!is_encrypted)
        {
            throw new Acquire.RemoteFunctionCallError(
                "Cannot unpack result as should be signed, but isn't. " +
                "Only encrypted results can be signed");
        }

        if (!("signature" in data))
        {
            throw new Acquire.RemoteFunctionCallError(
                "We requested the data was signed, but no signature found!");
        }

        signature = Acquire.string_to_bytes(data["signature"]);
    }

    if (is_encrypted)
    {
        let encrypted_data = Acquire.string_to_bytes(data["data"]);

        if (signature != undefined)
        {
            await public_cert.verify(signature, encrypted_data);
        }

        let fingerprint = data["fingerprint"];

        let my_fingerprint = await key.fingerprint();

        if (fingerprint != my_fingerprint)
        {
            throw new Acquire.RemoteFunctionCallError(
                "Cannot decrypt result - conflicting fingerprints " +
                `${fingerprint} versus ${my_fingerprint}`);
        }

        let decrypted_data = await key.decrypt(encrypted_data);
        decrypted_data = JSON.parse(decrypted_data);

        return await Acquire.unpack_arguments(
                                      {args:decrypted_data,
                                       is_return_value:is_return_value,
                                       func:func, service:service});
    }

    if (payload == undefined)
    {
        throw new Acquire.RemoteFunctionCallError(
            "Strange - no payload by this point in the call?");
    }

    return payload["return"];
}

Acquire.unpack_return_value = async function(
                                   {return_value=undefined,
                                    key=undefined, public_cert=undefined,
                                    func=undefined, service=undefined})
{
    return await Acquire.unpack_arguments(
                                  {args:return_value,
                                   key:key, public_cert:public_cert,
                                   is_return_value:true,
                                   func:func, service:service});
}

Acquire.pack_return_value = async function(
                                 {func=undefined, payload=undefined,
                                  key=undefined, response_key=undefined,
                                  public_cert=undefined,
                                  private_cert=undefined})
{
    if (func == undefined)
    {
        func = payload["function"];
    }

    let result = {};

    let now = Acquire.get_datetime_now_to_string();

    result["function"] = func;
    result["payload"] = payload;
    result["synctime"] = now;

    if (response_key != undefined)
    {
        let bytes = await response_key.bytes();
        bytes = Acquire.string_to_utf8_bytes(bytes);
        bytes = Acquire.bytes_to_string(bytes);
        result["encryption_public_key"] = bytes;

        if (public_cert != undefined)
        {
            let fingerprint = await public_cert.fingerprint();
            result["sign_with_service_key"] = fingerprint;
        }
    }

    let result_json = JSON.stringify(result);

    if (key != undefined)
    {
        // encrypt what we send to the server
        let result_data = await key.encrypt(result_json);
        let fingerprint = await key.fingerprint();

        result = {};
        result["data"] = Acquire.bytes_to_string(result_data);
        result["encrypted"] = true;
        result["fingerprint"] = fingerprint;
        result["synctime"] = now;
        result_json = JSON.stringify(result);
    }

    return result_json;
}

Acquire.pack_arguments = async function(
                              {func=undefined, args=undefined,
                               key=undefined, response_key=undefined,
                               public_cert=undefined})
{
    return await Acquire.pack_return_value(
                                   {func:func, payload:args,
                                    key:key, response_key:response_key,
                                    public_cert:public_cert});
}

/** Call the specified URL */
Acquire.call_function = async function(
                             {service_url=undefined, func=undefined,
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
        args_json = await Acquire.pack_arguments(
                                    {func:func, args:args, key:args_key});
    }
    else
    {
        var pubkey = await response_key.public_key();
        args_json = await Acquire.pack_arguments(
                                         {func:func, args:args, key:args_key,
                                          response_key:pubkey,
                                          public_cert:public_cert});
    }

    var response = null;

    try
    {
        response = await fetch(service_url,
                        {method: 'post',
                         headers: {
                            'Accept': 'application/json, test/plain, */*',
                            'Access-Control-Allow-Origin': '*',
                            'Content-Type': 'application/json'
                         },
                         body: args_json});

        response = await response.json();
    }
    catch(err)
    {
        throw new Acquire.RemoteFunctionCallError(
            `Error calling function ${service_url}`, err);
    }

    var result = undefined;

    try
    {
        result = JSON.parse(response);
    }
    catch(err)
    {
        throw new Acquire.RemoteFunctionCallError(
            `Error extracting json from function ${service_url}`, err);
    }

    try
    {
        result = await Acquire.unpack_return_value(
                            {return_value:result, key:response_key,
                             public_cert:public_cert, func:func,
                             service:service_url});
    }
    catch(err)
    {
        throw new Acquire.RemoteFunctionCallError(
            `Error upacking result from function ${service_url}`, err);
    }

    return result;
}
