/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

async function login()
{
    try
    {
        var username = document.getElementById("username").value;
        var password = document.getElementById("password").value;
        var otpcode = document.getElementById("otpcode").value;
        var remember_device = document.getElementById("remember_device").value;
        var url = document.getElementById("url").value;

        var wallet = new Wallet();
        await wallet.send_password({url:url, username:username,
                                    password:password, otpcode:otpcode,
                                    remember_device: remember_device});

        console.log("LOGIN SUCCESS!");
    }
    catch(err)
    {
        console.log(`LOGIN FAILED: ${err}`);
        console.log(err);
        var obj = JSON.parse(JSON.stringify(err));
        console.log(obj);
    }
}

async function test_acquire()
{
    try
    {
        /*var wallet = new Wallet();

        //wallet.clear();

        var service = await wallet.get_service({service_uid:"a0-a0"});

        console.log(service);

        service = await wallet.get_service({service_url:service.canonical_url()});

        console.log(service);

        id_service = await wallet.get_service({service_uid:"a0-a1"});

        console.log(id_service);*/

        /*user = new User({username:"chryswoods"});

        console.log(user);

        result = await user.request_login();

        console.log(user);

        console.log(result);*/
    }
    catch(err)
    {
        console.log(`UNCAUGHT EXCEPTION`);
        console.log(err);
        var obj = JSON.parse(JSON.stringify(err));
        console.log(obj);
    }
}
