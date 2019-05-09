/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

async function test_acquire()
{
    service_url = root_server["a0-a0"]["service_url"];
    console.log(service_url);

    var response = await call_function({service_url: service_url});

    console.log(response);

    var s = await Service.from_data(response["service_info"]);
    console.log(s);
    var data = await s.to_data();
    console.log(data);
    console.log(s.registry_uid());
    var s2 = await Service.from_data(data);
    console.log(s2);
}
