

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
    console.log(`unpack_arguments ${args}`);
    console.log(args);

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
        //lots to do here
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

    console.log(`function = ${func}`);

    result = {};

    var now = get_datetime_now_to_string();

    result["function"] = func;
    result["payload"] = payload;
    result["synctime"] = now;

    return JSON.stringify(result);
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

    console.log(`call_function args_json = ${args_json}`);

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
        console.log(`ERROR CALLING FUNCTION ${service_url} ${body}`);
        console.log(`ERROR == ${err}`);
        return undefined;
    }

    var result = undefined;

    try
    {
        result = JSON.parse(response);
    }
    catch(err)
    {
        console.log(`ERROR CALLING FUNCTION ${service_url} ${args_json}`);
        console.log(`ERROR EXTRACTING JSON ${response}`);
        console.log(`ERROR = ${err}`);
        return undefined;
    }

    return await unpack_return_value({return_value:result, key:response_key,
                                      public_cert:public_cert, func:func,
                                      service:service_url});
}
