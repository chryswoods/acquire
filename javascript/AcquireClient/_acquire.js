'use strict'

/** Holder for the Acquire "namespace" */
let Acquire = {};

/** "namespace" for all of the private Acquire classes/functions */
Acquire.Private = {};

/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

Acquire.login = async function ()
{
    try
    {
        let username = document.getElementById("username").value;
        let password = document.getElementById("password").value;
        let otpcode = document.getElementById("otpcode").value;
        let remember_device = document.getElementById("remember_device").value;
        let url = document.getElementById("url").value;

        let wallet = new Acquire.Wallet();
        await wallet.send_password({url:url, username:username,
                                    password:password, otpcode:otpcode,
                                    remember_device: remember_device});

        console.log("LOGIN SUCCESS!");
    }
    catch(err)
    {
        console.log(`LOGIN FAILED: ${err}`);
        console.log(err);
        let obj = JSON.parse(JSON.stringify(err));
        console.log(obj);
    }
}

Acquire.test_acquire = async function()
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
        let obj = JSON.parse(JSON.stringify(err));
        console.log(obj);
    }
}
