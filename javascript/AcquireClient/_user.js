
Acquire.Private._get_identity_url = function()
{
    return "fn.acquire-aaai.com";
}

Acquire.Private._get_identity_service = async function(
                                            {identity_url=undefined})
{
    if (identity_url == undefined)
    {
        identity_url = Acquire.Private._get_identity_url();
    }

    let wallet = new Acquire.Wallet();
    let service = undefined;

    try
    {
        service = await wallet.get_service({service_url:identity_url});
    }
    catch(err)
    {
        throw new Acquire.LoginError(
            `Have not received the identity service info from ` +
            `the identity service at '${identity_url}'`, err);
    }

    if (!service.can_identify_users())
    {
        throw new LoginError(
            `You can only use a valid identity service to log in! ` +
            `The service at '${identity_url}' is a ` +
            `'${service.service_type()}`);
    }

    return service;
}

/** Mirror of the Python Acquire.Client.User class */
Acquire.User = class
{
    constructor({username=undefined, identity_url=undefined,
                 identity_uid=undefined, scope=undefined,
                 permissions=undefined, auto_logout=true} = {})
    {
        this._username = username;
        this._status = "EMPTY";
        this._identity_service = undefined;
        this._scope = scope;
        this._permissions = permissions;

        if (identity_url != undefined)
        {
            this._identity_url = identity_url;
        }

        if (identity_uid != undefined)
        {
            this._identity_uid = identity_uid;
        }
        else
        {
            this._identity_uid = undefined;
        }

        this._user_uid = undefined;

        if (auto_logout)
        {
            this._auto_logout = true;
        }
        else
        {
            this._auto_logout = false;
        }
    }

    onDestroy()
    {
        if (this._auto_logout)
        {
            this.logout();
        }
    }

    _set_status(status)
    {
        if (status == "approved")
        {
            this._status = "LOGGED_IN";
        }
        else if (status == "denied")
        {
            this._status = this._set_error_state(
                        "Permission to log in was denied!");
        }
        else if (status == "logged_out")
        {
            this._status = "LOGGED_OUT";
        }
    }

    is_null()
    {
        return this._username != undefined;
    }

    username()
    {
        return this._username;
    }

    uid()
    {
        if (this.is_null())
        {
            return undefined;
        }

        if (this._user_uid == undefined)
        {
            throw new Acquire.PermissionError(
                "You cannot get the user UID until after you have logged in");
        }

        this._user_uid;
    }

    guid()
    {
        var user_uid = this.uid();
        var service_uid = this.identity_service().uid();
        return `${user_uid}@${service_uid}`;
    }

    status()
    {
        this._status;
    }

    _check_for_error()
    {
        if (this._status == "ERROR")
        {
            throw new Acquire.LoginError(this._error_string);
        }
    }

    _set_error_state(message)
    {
        this._status = "ERROR";
        this._error_string = message;
    }

    session_key()
    {
        this._check_for_error();

        try
        {
            this._session_key;
        }
        catch(_err)
        {
            return undefined;
        }
    }

    signing_key()
    {
        this._check_for_error();

        try
        {
            this._signing_key;
        }
        catch(_err)
        {
            return undefined;
        }
    }

    async identity_service()
    {
        if (this._identity_service != undefined)
        {
            return this._identity_service;
        }

        let identity_service = undefined;

        try
        {
            identity_service = await Acquire.Private._get_identity_service(
                                {identity_url:this.identity_service_url()});
        }
        catch(err)
        {
            throw new Acquire.LoginError(
                `Unable to get the identity service at ` +
                `'${this.identity_service_url()}'`, err);
        }

        if (this._identity_uid != undefined)
        {
            if (identity_service.uid() != this._identity_uid)
            {
                throw new Acquire.LoginError(
                    `The UID of the identity service at ` +
                    `'${this.identity_service_url()}', which is ` +
                    `${identity_service.uid()}, does not match that ` +
                    `supplied by the user, '${this._identity_uid}'. ` +
                    `You should double-check that the UID is correct, or ` +
                    `that you have supplied the correct identity_url`);
            }
        }
        else
        {
            this._identity_uid = identity_service.uid();
        }

        this._identity_service = identity_service;

        return this._identity_service;
    }

    identity_service_uid()
    {
        if (this._identity_uid != undefined)
        {
            return this._identity_uid;
        }
        else
        {
            return this._identity_service.uid();
        }
    }

    identity_service_url()
    {
        this._check_for_error();

        try
        {
            return this._identity_url;
        }
        catch(_err)
        {
            return _get_identity_url();
        }
    }

    login_url()
    {
        this._check_for_error();

        try
        {
            return this._login_url;
        }
        catch(_err)
        {
            return undefined;
        }
    }

    login_qr_code()
    {
        return Acquire.Private._create_qrcode(this._login_url);
    }

    scope()
    {
        return this._scope;
    }

    permissions()
    {
        return this._permissions;
    }

    session_uid()
    {
        this._check_for_error();

        try
        {
            return this._session_uid;
        }
        catch(_err)
        {
            return undefined;
        }
    }

    is_empty()
    {
        return this._status == "EMPTY";
    }

    is_logged_in()
    {
        return this._status == "LOGGED_IN";
    }

    is_logging_in()
    {
        return this._status == "LOGGING_IN";
    }

    async logout()
    {
        if (this.is_logged_in() | this.is_logging_in())
        {
            let service = this.identity_service();

            let args = {"session_uid": this._session_uid}

            if (this.is_logged_in())
            {
                let authorisation = new Acquire.Authorisation(
                                    {resource:`logout ${this._session_uid}`,
                                     user:this});
                args["authorisation"] = authorisation.to_data();
            }
            else
            {
                let resource = `logout ${this._session_uid}`;
                let signature = await this.signing_key().sign(resource);
                args["signature"] = Acquire.bytes_to_string(signature);
            }

            result = await service.call_function({func:"logout", args:args});

            this._status = "LOGGED_OUT";

            return result
        }
    }

    static async register({username=undefined,
                           password=undefined,
                           identity_url=undefined})
    {
        let service = Acquire.Private._get_identity_service(
                                            {identity_url:identity_url});

        let encoded_password = await Acquire.Credentials.encode_password(
                                    {identity_uid:service.uid(),
                                     password:password});

        let args = {"username": username,
                    "password": encoded_password}

        let result = await service.call_function({func:"register", args:args});

        let provisioning_uri = undefined;

        try
        {
            provisioning_uri = result["provisioning_uri"];
        }
        catch(_err)
        {
            throw new UserError(
                `Cannot register the user '${username}' on ` +
                `the identity service at '${identity_url}'!`);
        }

        result = {}
        result["provisioning_uri"] = provisioning_uri

        try
        {
            let otpsecret = re.search('secret=([\w\d+]+)&issuer',
                                  provisioning_uri).groups()[0];
            result["otpsecret"] = otpsecret;
        }
        catch(_err)
        {}

        try
        {
            result["qrcode"] = Acquire.Private._create_qrcode(
                                                        provisioning_uri);
        }
        catch(_err)
        {}

        return result;
    }

    async request_login()
    {
        this._check_for_error();

        if (!this.is_empty())
        {
            throw new Acquire.LoginError(
                "You cannot try to log in twice using the same " +
                "User object. Create another object if you want " +
                "to try to log in again.");
        }

        try
        {
            let session_key = new Acquire.PrivateKey();
            let signing_key = new Acquire.PrivateKey();

            let public_session_key = await session_key.public_key();
            let public_signing_key = await signing_key.public_key();

            let session_key_data = await public_session_key.to_data();
            let signing_key_data = await public_signing_key.to_data();

            let args = {"username": this._username,
                        "public_key": session_key_data,
                        "public_certificate": signing_key_data,
                        "scope": this._scope,
                        "permissions": this._permissions
                    };

            try
            {
                let hostname = socket.gethostname();
                let ipaddr = socket.gethostbyname(hostname);
                args["hostname"] = hostname;
                args["ipaddr"] = ipaddr;
            }
            catch(_err)
            {}

            let identity_service = await this.identity_service();
            let result = undefined;

            result = await identity_service.call_function(
                                        {func:"request_login", args:args});

            var login_url = undefined;

            try
            {
                login_url = result["login_url"];
            }
            catch(_err)
            {}

            if (login_url == undefined)
            {
                error = `Failed to login. Could not extract the login URL! ` +
                        `Result is ${result}`;
                this._set_error_state(error);
                throw new Acquire.LoginError(error);
            }

            let session_uid = undefined;

            try
            {
                session_uid = result["session_uid"];
            }
            catch(_err)
            {}

            if (session_uid == undefined)
            {
                error = `Failed to login. Could not extract the login ` +
                        `session UID! Result is ${result}`;

                this._set_error_state(error);
                throw new Acquire.LoginError(error);
            }

            this._login_url = result["login_url"];
            this._session_key = session_key;
            this._signing_key = signing_key;
            this._session_uid = session_uid;
            this._status = "LOGGING_IN";
            this._user_uid = undefined;

            var short_uid = session_uid.substring(0,8);

            return {"login_url": this._login_url,
                    "session_uid": session_uid,
                    "short_uid": short_uid};
        }
        catch(err)
        {
            error = "Could not complete login!";
            this._set_error_state(error);
            throw new Acquire.LoginError(error, err);
        }
    }

    async _poll_session_status()
    {
        let ervice = this.identity_service();

        let args = {"session_uid": this._session_uid};

        let result = await service.call_function({func:"get_session_info",
                                                  args:args});

        let status = result["session_status"];
        this._set_status(status);

        if (this.is_logged_in())
        {
            if (this._user_uid == undefined)
            {
                let user_uid = result["user_uid"];
                assert(user_uid != undefined);
                this._user_uid = user_uid;
            }
        }
    }

    async wait_for_login({timeout=undefined, polling_delta=5})
    {
        this._check_for_error();

        if (!this.is_logging_in())
        {
            return this.is_logged_in();
        }

        polling_delta = int(polling_delta);
        if (polling_delta > 60)
        {
            polling_delta = 60;
        }
        else if (polling_delta < 1)
        {
            polling_delta = 1;
        }

        if (timeout == undefined)
        {
            while (true)
            {
                await this._poll_session_status();

                if (this.is_logged_in())
                {
                    return true;
                }
                else if (!this.is_logging_in())
                {
                    return false;
                }

                time.sleep(polling_delta);
            }
        }
        else
        {
            timeout = int(timeout);

            if (timeout < 1)
            {
                timeout = 1;
            }

            let start_time = get_datetime_now();

            while ((get_datetime_now() - start_time).seconds < timeout)
            {
                await this._poll_session_status();

                if (this.is_logged_in())
                {
                    return true;
                }
                else if (!this.is_logging_in())
                {
                    return false;
                }

                time.sleep(polling_delta);
            }

            return false
        }
    }
}
