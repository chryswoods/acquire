/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

async function test_acquire()
{
    var service_url = root_server["a0-a0"]["service_url"];
    var pubkey = await PublicKey.from_data(
                        root_server["a0-a0"]["public_key"]);
    var pubcert = await PublicKey.from_data(
                        root_server["a0-a0"]["public_certificate"])

    var func = "get_service";
    var args = {"service_uid": "a0-a0"};

    var response_key = new PrivateKey();

    var response = await call_function({service_url: service_url,
                                        func:func, args:args,
                                        args_key:pubkey,
                                        response_key:response_key});

    var s = await Service.from_data(response["service_data"]);
    console.log(s);
}
