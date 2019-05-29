
/** Write local data to the browser with 'name' == 'value' */
Acquire.Private._writeWalletData = function(name, value)
{
    if (typeof(Storage) != "undefined")
    {
        let key = `Acquire/Wallet/${name}`;
        localStorage.setItem(key, value);
        //console.log(`SAVED ${key} = ${value}`);
    }
}

/** Remove local data at key 'name' */
Acquire.Private._clearWalletData = function(name)
{
    if (typeof(Storage) != "undefined")
    {
        let key = `Acquire/Wallet/${name}`;
        console.log(`REMOVE KEY ${key}`);
        return localStorage.removeItem(key);
    }
}

/** Read local data from the browser at key 'name'. Returns
 *  NULL if no such data exists
 */
Acquire.Private._readWalletData = function(name)
{
    if (typeof(Storage) != "undefined")
    {
        let key = `Acquire/Wallet/${name}`;
        let value = localStorage.getItem(key);
        //console.log(`READ ${key} == ${value}`);
        return value;
    }
    else
    {
        return undefined;
    }
}

/** https://stackoverflow.com/questions/901115/
 *          how-can-i-get-query-string-values-in-javascript */
Acquire.Private._getParameterByName = function(name, url)
{
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, '\\$&');
    let regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
    let results = regex.exec(url);
    if (!results) return undefined;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

Acquire.Wallet = class
{
    constructor()
    {}

    /** Clear the wallet */
    clear()
    {
        for (let key in localStorage)
        {
            if (key.startsWith("Acquire/Wallet"))
            {
                console.log(`Deleting ${key}`);
                localStorage.removeItem(key);
            }
        }
    }

    /** Save the passed service to browser storage */
    async _save_service(service)
    {
        let data = await service.to_data();
        data = JSON.stringify(data);
        Acquire.Private._writeWalletData(`service_uid/${service.uid()}`, data);
        let url = Acquire.string_to_safestring(service.canonical_url());
        Acquire.Private._writeWalletData(`service_url/${url}`, service.uid());
    }

    async _get_trusted_registry_service()
    {
        //have we loaded the central registry before?
        try
        {
            let registry = await this.get_service({service_uid:"a0-a0",
                                                   autofetch:false});
            return registry;
        }
        catch(err)
        {}

        try
        {
            //we need to bootstrap to get the registry
            let registry_url = Acquire.root_server["a0-a0"]["service_url"];
            let registry_pubkey = await Acquire.PublicKey.from_data(
                            Acquire.root_server["a0-a0"]["public_key"]);
            let registry_pubcert = await Acquire.PublicKey.from_data(
                            Acquire.root_server["a0-a0"]["public_certificate"])

            let func = "get_service";
            let args = {"service_uid": "a0-a0"};

            let response_key = Acquire.get_private_key("function");
            let response = await Acquire.call_function(
                                            {service_url: registry_url,
                                                func:func, args:args,
                                                args_key:registry_pubkey,
                                                public_cert:registry_pubcert,
                                                response_key:response_key});

            let registry = await Acquire.Service.from_data(
                                                response["service_info"]);
            await this._save_service(registry);
            return registry;
        }
        catch(err)
        {
            throw new Acquire.ServiceError(
                "Failed to connect to the trusted registry service a0-a0",
                err);
        }
    }

    async get_service({service_uid=undefined, service_url=undefined,
                       service_type=undefined, autofetch=true})
    {
        let service = undefined;

        if (!service_url)
        {
            if (!service_uid)
            {
                throw new Acquire.PermissionError(
                    "You need to specify one of service_url or service_uid");
            }

            //look up from storage if we have seen this service before
            let data = Acquire.Private._readWalletData(
                                    `service_uid/${service_uid}`);

            if (data)
            {
                try
                {
                    data = JSON.parse(data);
                    service = await Acquire.Service.from_data(data);
                }
                catch(_err)
                {
                    //possible corruption of local store
                    console.log("LOCAL STORAGE CORRUPTION?");
                    console.log(_err);
                    service = undefined;
                }
            }
        }
        else if (service_url)
        {
            let url = Acquire.string_to_safestring(service_url);
            let suid = Acquire.Private._readWalletData(
                                            `service_url/${url}`);

            if (suid)
            {
                let data = Acquire.Private._readWalletData(
                                            `service_uid/${suid}`);
                if (data)
                {
                    try
                    {
                        data = JSON.parse(data);
                        service = await Acquire.Service.from_data(data);
                    }
                    catch(_err)
                    {
                        //possible corruption of local store
                        console.log("LOCAL STORAGE CORRUPTION?");
                        console.log(_err);
                        service = undefined;
                    }
                }
            }
        }

        let must_write = false;

        if (!service)
        {
            if (!autofetch)
            {
                throw new Acquire.ServiceError(
                    `No service at ${service_url} : ${service_uid}`);
            }

            // we now need to connect to a trusted registry
            let registry = undefined;

            try
            {
                registry = await this._get_trusted_registry_service(
                                              {service_uid:service_uid,
                                               service_url:service_url});
            }
            catch(err)
            {
                throw new Acquire.ServiceError(
                    `Cannot get service ${service_uid} : ${service_url} ` +
                    `because we can't load the registry!`, err);
            }

            try
            {
                service = await registry.get_service(
                                                {service_uid:service_uid,
                                                 service_url:service_url});
            }
            catch(err)
            {
                throw new Acquire.ServiceError(
                    `Cannot get service ${service_uid} : ${service_url} ` +
                    `because of error`, err);
            }

            must_write = true;
        }

        if (service_type)
        {
            if (service.service_type() != service_type)
            {
                throw new Acquire.ServiceError(
                    `Disagreement of service type for ${service}. ` +
                    `Expected ${service_type} but got ` +
                    `${service.service_type()}`);
            }
        }

        if (service.should_refresh_keys())
        {
            await service.refresh_keys();
            must_write = true;
        }

        if (must_write)
        {
            //save this service to storage
            await this._save_service(service);
        }

        return service;
    }

    async _find_userinfo({username, password, service_uid})
    {
        // for security, the key for the userinfo is a hash
        // of the username + password + service_uid
        let key = Acquire.multi_md5(service_uid, username+":"+password);

        key = `Acquire/wallet/userinfo/${key}`;

        let userinfo = localStorage.getItem(key);

        if (!userinfo)
        {
            return {};
        }

        userinfo = Acquire.string_to_bytes(userinfo);

        // the data in this userinfo is encrypted using a SymmetricKey
        // whose password is the MD5 combination of the service_uid
        // and the user password
        let passkey = Acquire.multi_md5(service_uid, password);
        let symkey = new Acquire.SymmetricKey({symmetric_key:passkey});

        try
        {
            userinfo = await symkey.decrypt(userinfo);
            return JSON.parse(userinfo);
        }
        catch(err)
        {
            console.log("Could not decrypt the userinfo!");
            console.log(err);
            let obj = JSON.parse(JSON.stringify(err));
            console.log(obj);
            return {};
        }
    }

    async _set_userinfo({userinfo, username, password, service_uid})
    {
        try
        {
            userinfo = JSON.stringify(userinfo);

            // the data in this userinfo is encrypted using a SymmetricKey
            // whose password is the MD5 combination of the service_uid
            // and the user password
            let passkey = Acquire.multi_md5(service_uid, password);
            let symkey = new Acquire.SymmetricKey({symmetric_key:passkey});

            userinfo = await symkey.encrypt(userinfo);
            userinfo = Acquire.bytes_to_string(userinfo);

            // for security, the key for the userinfo is a hash
            // of the username + password + service_uid
            let key = Acquire.multi_md5(service_uid, username+":"+password);
            key = `Acquire/wallet/userinfo/${key}`;

            localStorage.setItem(key, userinfo);
        }
        catch(err)
        {
            console.log("Could not remember the device info");
            console.log(err);
            let obj = JSON.parse(JSON.stringify(err));
            console.log(obj);
        }
    }

    static get_login_details_from_url(url)
    {
        // the login URL is http[s]://something.com?id=XXXX/YY.YY.YY.YY
        // where XXXX is the service_uid of the service we should
        // connect with, and YY.YY.YY.YY is the short_uid of the login
        let idcode = undefined;

        try
        {
            idcode = Acquire.Private._getParameterByName('id', url);
        }
        catch(err)
        {
            throw new Acquire.LoginError(
                `Cannot identify the session of service information ` +
                `from the login URL ${url}. This should have ` +
                `id=XX-XX/YY.YY.YY.YY as a query parameter.`, err);
        }

        let service_uid, short_uid = undefined;

        try
        {
            let result = idcode.split("/");
            service_uid = result[0];
            short_uid = result[1];
        }
        catch(err)
        {
            throw new Acquire.LoginError(
                `Cannot identify the session of service information ` +
                `from the login URL ${url}. This should have ` +
                `id=XX-XX/YY.YY.YY.YY as a query parameter.`, err);
        }

        return [service_uid, short_uid];
    }

    async _get_user_password({userinfo=undefined})
    {
        throw new Acquire.LoginError(
                    "You must supply a username and password!");
    }

    async _get_otpcode({userinfo=undefined})
    {
        let otpsecret = userinfo["otpsecret"];

        if (!otpsecret)
        {
            throw new Acquire.LoginError(
                    "You must supply an OTPCode");
        }

        let otp = new Acquire.TOTP();
        let otpcode = otp.getOTP(otpsecret);
        console.log(`SUBMITTING CODE ${otpcode}`);
        return otpcode;
    }

    async send_password({url=undefined, username=undefined,
                         password=undefined, otpcode=undefined,
                         remember_device=false, dryrun=false,
                         service=undefined, short_uid=undefined})
    {
        if (!service)
        {
            let service_uid = undefined;
            [service_uid, short_uid] =
                        Acquire.Wallet.get_login_details_from_url(url);

            // now get the service
            try
            {
                service = await this.get_service({service_uid:service_uid});
            }
            catch(err)
            {
                throw new Acquire.LoginError(
                    `Cannot find the service with UID ${service_uid}`, err);
            }
        }

        if (!short_uid)
        {
            throw new Acquire.LoginError(
                "You need to specify the short_uid of the login session!");
        }

        if (!service.can_identify_users())
        {
            throw new Acquire.LoginError(
                `Service ${service} is unable to identify users! ` +
                `You cannot log into something that is not a valid ` +
                `identity service!`);
        }

        let userinfo = await this._find_userinfo({username:username,
                                                  password:password,
                                                  service_uid:service.uid()});

        if (!username)
        {
            try
            {
                username = userinfo["username"];
            }
            catch(_err)
            {
                throw new Acquire.LoginError("You must supply the username!");
            }

            if (!username)
            {
                throw new Acquire.LoginError("You must supply the username!");
            }
        }

        let user_uid = undefined;

        if ("user_uid" in userinfo)
        {
            user_uid = userinfo["user_uid"];
        }

        let device_uid = undefined;

        if ("device_uid" in userinfo)
        {
            device_uid = userinfo["device_uid"];
        }

        if (password == undefined)
        {
            password = await this._get_user_password({userinfo:userinfo});
        }

        if (otpcode == undefined)
        {
            otpcode = await this._get_otpcode({userinfo:userinfo});
        }
        else
        {
            // user if providing the primary OTP, so this is not a device
            device_uid = undefined;
        }

        console.log(`device_uid = ${device_uid}`);

        console.log(`Logging in to ${service.canonical_url()}, ` +
                    `session ${short_uid} with username ${username}...`);

        if (dryrun)
        {
            console.log(`Calling ${service.canonical_url} with username=` +
                        `${username}, password=${password}, otpcode=` +
                        `${otpcode}, remember_device=${remember_device}, ` +
                        `device_uid=${device_uid}, short_uid=${short_uid}, ` +
                        `user_uid=${user_uid}`);
            return;
        }

        let response = undefined;

        try
        {
            let creds = new Acquire.Credentials(
                                        {username:username, password:password,
                                         otpcode:otpcode, short_uid:short_uid,
                                         device_uid:device_uid});

            let cred_data = await creds.to_data({identity_uid:service.uid()});

            let args = {"credentials": cred_data,
                        "user_uid": user_uid,
                        "remember_device": remember_device,
                        "short_uid": short_uid}

            response = await service.call_function({func:"login",
                                                    args:args});
        }
        catch(err)
        {
            throw new Acquire.LoginError("Failed to log in", err);
        }

        if (!remember_device)
        {
            return;
        }

        try
        {
            let returned_user_uid = response["user_uid"];

            if (returned_user_uid != user_uid)
            {
                // change of user?
                userinfo = {};
                user_uid = returned_user_uid;
            }
            else
            {
                userinfo["user_uid"] = user_uid;
            }
        }
        catch(_err)
        {}

        userinfo["username"] = username;

        try
        {
            userinfo["device_uid"] = response["device_uid"];
        }
        catch(_err)
        {}

        try
        {
            userinfo["otpsecret"] = response["otpsecret"];
        }
        catch(_err)
        {}

        await this._set_userinfo({userinfo:userinfo,
                                  username:username,
                                  password:password,
                                  service_uid:service.uid()});
    }
}