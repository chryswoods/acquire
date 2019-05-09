/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

async function test_acquire()
{
    var k = new PrivateKey();
    var p = await k.public_key();
    var b = await p.bytes();
    console.log(`bytes = ${b}`);
    console.log(`fingerprint = ${await p.fingerprint()}`);

    console.log(JSON.stringify(await p.to_data()));

    return;

    service_url = root_server["a0-a0"]["service_url"];

    var response = await call_function({service_url: service_url});

    console.log(response);

    var s = await Service.from_data(response["service_info"]);
    console.log(s);

    var data = await s.to_data();
    console.log(JSON.stringify(data));
}
