

function _get_identity_url()
{
    return "fn.acquire-aaai.com";
}

async function _get_identity_service({identity_url=undefined})
{
    if (identity_url == undefined)
    {
        identity_url = _get_identity_url();
    }

    var wallet = new Wallet();
    var service = undefined;

    try
    {
        service = await wallet.get_service({service_url:identity_url});
    }
    catch(err)
    {
        throw new LoginError(
            `Have not received the identity service info from ` +
            `the identity service at '${identity_url}'\n\nCAUSE: ${err}`);
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
class User
{
    constructor({username=undefined, identity_url=undefined,
                 identity_uid=undefined, scope=undefined,
                 permissions=undefined, auto_logout=true})
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
            throw new PermissionError(
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
            throw new LoginError(this._error_string);
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

        var identity_service = await _get_identity_service(
                                {identity_url:this.identity_service_url()});

        if (this._identity_uid != undefined)
        {
            if (identity_service.uid() != this._identity_uid)
            {
                throw new LoginError(
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
        return _create_qrcode(this._login_url);
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
            service = this.identity_service();

            args = {"session_uid": this._session_uid}

            if (this.is_logged_in())
            {
                authorisation = new Authorisation(
                                    {resource:`logout ${this._session_uid}`,
                                     user:this});
                args["authorisation"] = authorisation.to_data();
            }
            else
            {
                resource = `logout ${this._session_uid}`;
                signature = await this.signing_key().sign(resource);
                args["signature"] = bytes_to_string(signature);
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
        service = _get_identity_service({identity_url:identity_url});

        encoded_password = await Credentials.encode_password(
                                    {identity_uid:service.uid(),
                                     password:password});

        args = {"username": username,
                "password": encoded_password}

        result = await service.call_function({func:"register", args:args});

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
            otpsecret = re.search('secret=([\w\d+]+)&issuer',
                                  provisioning_uri).groups()[0];
            result["otpsecret"] = otpsecret;
        }
        catch(_err)
        {}

        try
        {
            result["qrcode"] = _create_qrcode(provisioning_uri);
        }
        catch(_err)
        {}

        return result;
    }

    async request_login()
    {
        try
        {
        this._check_for_error();

        if (!this.is_empty())
        {
            throw new LoginError(
                "You cannot try to log in twice using the same " +
                "User object. Create another object if you want " +
                "to try to log in again.");
        }

        var session_key = new PrivateKey();
        var signing_key = new PrivateKey();

        var public_session_key = await session_key.public_key();
        var public_signing_key = await signing_key.public_key();

        var session_key_data = await public_session_key.to_data();
        var signing_key_data = await public_signing_key.to_data();

        var args = {"username": this._username,
                    "public_key": session_key_data,
                    "public_certificate": signing_key_data,
                    "scope": this._scope,
                    "permissions": this._permissions
                   };

        try
        {
            hostname = socket.gethostname();
            ipaddr = socket.gethostbyname(hostname);
            args["hostname"] = hostname;
            args["ipaddr"] = ipaddr;
        }
        catch(_err)
        {}

        var identity_service = await this.identity_service();

        var result = await identity_service.call_function(
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
            throw new LoginError(error);
        }

        session_uid = undefined;

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
            throw new LoginError(error);
        }

        console.log("HERE");

        this._login_url = result["login_url"];
        this._session_key = session_key;
        this._signing_key = signing_key;
        this._session_uid = session_uid;
        this._status = "LOGGING_IN";
        this._user_uid = undefined;

        return {"login_url": this._login_url,
                "session_uid": session_uid,
                "short_uid": LoginSession.to_short_uid(session_uid)};
        }
        catch(err)
        {
            console.log(err);
        }
    }

    async _poll_session_status()
    {
        service = this.identity_service();

        args = {"session_uid": this._session_uid};

        result = await service.call_function({func:"get_session_info",
                                              args:args});

        status = result["session_status"];
        this._set_status(status);

        if (this.is_logged_in())
        {
            if (this._user_uid == undefined)
            {
                user_uid = result["user_uid"];
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

            start_time = get_datetime_now();

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
