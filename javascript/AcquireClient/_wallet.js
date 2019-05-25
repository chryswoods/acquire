
/** Write local data to the browser with 'name' == 'value' */
function _writeData(name, value)
{
    if (typeof(Storage) != "undefined")
    {
        localStorage.setItem(name, value);
    }
}

/** Remove local data at key 'name' */
function _clearData(name)
{
    if (typeof(Storage) !== "undefined")
    {
        return localStorage.removeItem(name);
    }
}

/** Read local data from the browser at key 'name'. Returns
 *  NULL if no such data exists
 */
function _readData(name)
{
    if (typeof(Storage) !== "undefined")
    {
        return localStorage.getItem(name);
    }
    else
    {
        return undefined;
    }
}

/** https://stackoverflow.com/questions/901115/
 *          how-can-i-get-query-string-values-in-javascript */
function _getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, '\\$&');
    var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

class Wallet
{
    constructor()
    {}

    /** Clear the wallet */
    clear()
    {
        localStorage.clear();
    }

    /** Save the passed service to browser storage */
    async _save_service(service)
    {
        var data = await service.to_data();
        data = JSON.stringify(data);
        _writeData(`wallet/service_uid/${service.uid()}`, data);
        var url = string_to_safestring(service.canonical_url());
        _writeData(`wallet/service_url/${url}`, service.uid());
    }

    async _get_trusted_registry_service({service_url=undefined,
                                         service_uid=undefined})
    {
        //have we loaded the central registry before?
        try
        {
            var registry = await this.get_service({service_uid:"a0-a0",
                                                   autofetch:false});
            return registry;
        }
        catch(err)
        {}

        //we need to bootstrap to get the registry
        var registry_url = root_server["a0-a0"]["service_url"];
        var registry_pubkey = await PublicKey.from_data(
                                     root_server["a0-a0"]["public_key"]);
        var registry_pubcert = await PublicKey.from_data(
                                   root_server["a0-a0"]["public_certificate"])

        var func = "get_service";
        var args = {"service_uid": "a0-a0"};

        var response_key = get_private_key("function");
        var response = await call_function({service_url: registry_url,
                                            func:func, args:args,
                                            args_key:registry_pubkey,
                                            public_cert:registry_pubcert,
                                            response_key:response_key});

        var registry = await Service.from_data(response["service_info"]);
        await this._save_service(registry);
        return registry;
    }

    async get_service({service_uid=undefined, service_url=undefined,
                       service_type=undefined, autofetch=true})
    {
        var service = undefined;

        if (service_url == undefined)
        {
            if (service_uid == undefined)
            {
                throw new PermissionError(
                    "You need to specify one of service_url or service_uid");
            }

            //look up from storage if we have seen this service before
            var data = _readData(`wallet/service_uid/${service_uid}`);

            if (data != undefined)
            {
                data = JSON.parse(data);
                service = await Service.from_data(data);
            }
        }
        else if (service_url != undefined)
        {
            var url = string_to_safestring(service_url);
            var suid = _readData(`wallet/service_url/${url}`);

            if (suid != undefined)
            {
                var data = _readData(`wallet/service_uid/${suid}`);
                if (data != undefined)
                {
                    data = JSON.parse(data);
                    service = await Service.from_data(data);
                }
            }
        }

        var must_write = false;

        if (service == undefined)
        {
            if (!autofetch)
            {
                throw new ServiceError(
                    `No service at ${service_url} : ${service_uid}`);
            }

            // we now need to connect to a trusted registry
            try
            {
                var registry = await this._get_trusted_registry_service(
                                              {service_uid:service_uid,
                                               service_url:service_url});
            }
            catch(err)
            {
                throw new ServiceError(
                    `Cannot get service ${service_uid} : ${service_url} ` +
                    `because we can't load the registry! ${err}`);
            }

            try
            {
                service = await registry.get_service(
                                                {service_uid:service_uid,
                                                 service_url:service_url});
            }
            catch(err)
            {
                throw new ServiceError(
                    `Cannot get service ${service_uid} : ${service_url} ` +
                    `because of error ${err}`);
            }

            must_write = true;
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

    async _find_userinfo({username=undefined, password=undefined})
    {
        /*userfiles = _glob.glob("%s/user_*_encrypted" % wallet_dir)

        userinfos = []

        for userfile in userfiles:
            try:
                userinfo = _read_json(userfile)
                if _could_match(userinfo, username, password):
                    userinfos.append((userinfo["username"], userinfo))
            except:
                pass

        userinfos.sort(key=lambda x: x[0])

        if len(userinfos) == 1:
            return self._unlock_userinfo(userinfos[0][1])

        if len(userinfos) == 0:
            if username is None:
                username = _input("Please type your username: ")

            userinfo = {"username": username}

            if password is not None:
                userinfo["password"] = password

            return userinfo

        _output("Please choose the account by typing in its number, "
                "or type a new username if you want a different account.")

        for (i, (username, userinfo)) in enumerate(userinfos):
            _output("[%d] %s {%s}" % (i+1, username, userinfo["user_uid"]))

        max_tries = 5

        for i in range(0, max_tries):
            reply = _input(
                    "\nMake your selection (1 to %d) " %
                    (len(userinfos))
                )

            try:
                idx = int(reply) - 1
            except:
                idx = None

            if idx is None:
                # interpret this as a username
                return self._find_userinfo(username=reply, password=password)
            elif idx < 0 or idx >= len(userinfos):
                _output("Invalid account.")
            else:
                return self._unlock_userinfo(userinfos[idx][1])

            if i < max_tries-1:
                _output("Try again...")

        userinfo = {}

        if username is not None:
            userinfo["username"] = username

        return userinfo*/

        return {};
    }

    _set_userinfo({userinfo=undefined, user_uid=undefined,
                   identity_uid=undefined})
    {}

    async send_password({url, username=undefined, password=undefined,
                         otpcode=undefined,
                         remember_device=false, dryrun=false})
    {
        // the login URL is http[s]://something.com?id=XXXX/YY.YY.YY.YY
        // where XXXX is the service_uid of the service we should
        // connect with, and YY.YY.YY.YY is the short_uid of the login
        try
        {
            var idcode = _getParameterByName('id', url);
        }
        catch(err)
        {
            throw new LoginError(
                `Cannot identify the session of service information ` +
                `from the login URL ${url}. This should have ` +
                `id=XX-XX/YY.YY.YY.YY as a query parameter.`, err);
        }

        try
        {
            var result = idcode.split("/");
            var service_uid = result[0];
            var short_uid = result[1];
        }
        catch(err)
        {
            throw new LoginError(
                `Cannot identify the session of service information ` +
                `from the login URL ${url}. This should have ` +
                `id=XX-XX/YY.YY.YY.YY as a query parameter.`, err);
        }

        // now get the service
        try
        {
            var service = await this.get_service({service_uid:service_uid});
        }
        catch(err)
        {
            throw new LoginError(
                `Cannot find the service with UID ${service_uid}`, err);
        }

        if (!service.can_identify_users())
        {
            throw new LoginError(
                `Service ${service} is unable to identify users! ` +
                `You cannot log into something that is not a valid ` +
                `identity service!`);
        }

        var userinfo = await this._find_userinfo({username:username,
                                                  password:password});

        if (!username)
        {
            try
            {
                username = userinfo["username"];
            }
            catch(_err)
            {
                throw new LoginError("You must supply the username!");
            }

            if (!username)
            {
                throw new LoginError("You must supply the username!");
            }
        }

        var user_uid = undefined;

        if ("user_uid" in userinfo)
        {
            user_uid = userinfo["user_uid"];
        }

        var device_uid = undefined;

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

        try
        {
            var creds = new Credentials({username:username, password:password,
                                         otpcode:otpcode, short_uid:short_uid,
                                         device_uid:device_uid});

            var cred_data = await creds.to_data({identity_uid:service.uid()});

            var args = {"credentials": cred_data,
                        "user_uid": user_uid,
                        "remember_device": remember_device,
                        "short_uid": short_uid}

            var response = await service.call_function({func:"login",
                                                        args:args});
        }
        catch(err)
        {
            throw new LoginError("Failed to log in", err);
        }

        if (!remember_device)
        {
            return;
        }

        try
        {
            var returned_user_uid = response["user_uid"];

            if (returned_user_uid != user_uid)
            {
                // change of user?
                userinfo = {};
                user_uid = returned_user_uid;
            }
        }
        catch(_err)
        {
            //no user_uid so nothing to save
            return;
        }

        if (!user_uid)
        {
            // can't save anything
            return;
        }

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

        this._set_userinfo({userinfo:userinfo,
                            user_uid:user_uid,
                            identity_uid:service.uid()});
    }
}