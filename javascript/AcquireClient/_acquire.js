/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

async function test_acquire()
{
    console.log(`NOW = ${get_datetime_now_to_string()}`);

    service_url = root_server["a0-a0"]["service_url"];

    var func = "get_service";
    var args = {"service_uid": "a0-a0"};

    var response = await call_function({service_url: service_url,
                                        func:func, args:args});

    console.log(response);

    var s = await Service.from_data(response["service_data"]);
    console.log(s);

    var data = await s.to_data();
    console.log(JSON.stringify(data));
}
