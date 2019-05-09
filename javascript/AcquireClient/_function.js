

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
