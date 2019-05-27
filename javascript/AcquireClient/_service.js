
Acquire.Private._private_keys = {};

/** Return the session-scoped private key called 'name' */
Acquire.get_private_key = function(name)
{
    if (name in Acquire.Private._private_keys)
    {
        return Acquire.Private._private_keys[name];
    }
    else
    {
        let private_key = new Acquire.PrivateKey();
        Acquire.Private._private_keys[name] = private_key;
        return private_key;
    }
}

/** Provide a handle around one of the remote Acquire Services.
 *  Use this class to manage the services, and to simplify secure
 *  calling of the service functions. This class strongly
 *  mirrors Acquire.Client.Service, so look to this for
 *  documentation
 */
Acquire.Service = class
{
    constructor({service_url=undefined, service_uid=undefined,
                 service_type=undefined} = {})
    {
        this._canonical_url = service_url;
        this._uid = service_uid;
        this._service_type = service_type;
    }

    is_null()
    {
        return this._uid == undefined;
    }

    uid()
    {
        return this._uid;
    }

    canonical_url()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            return this._canonical_url;
        }
    }

    service_url(prefer_https=true)
    {
        if (this.is_null()){ return undefined; }
        else
        {
            let scheme = "http";

            if (prefer_https && ("https" in this._schemes))
            {
                scheme = "https";
            }
            else
            {
                scheme = this._schemes[0];
            }

            let port = this._ports[scheme]

            if ((port == undefined) || (port.length == 0))
            {
                return `${scheme}://${this._domain}${this._path}`;
            }
            else
            {
                return `${scheme}://${this._domain}:${port}${this._path}`;
            }
        }
    }

    can_identify_users()
    {
        return true;
    }

    service_type()
    {
        if (this.is_null()){ return undefined; }
        else { return this._service_type; }
    }

    registry_uid()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            let root = this.uid().split("-")[0];
            return `${root}-${root}`;
        }
    }

    public_key()
    {
        if (this.is_null()){ return undefined; }
        else{ return this._pubkey;}
    }

    public_certificate()
    {
        if (this.is_null()){ return undefined; }
        else{ return this._pubcert;}
    }

    should_refresh_keys()
    {
        return false;
    }

    async get_service({service_uid=undefined, service_url=undefined})
    {
        if (this.is_null())
        {
            return undefined;
        }
        else if (service_uid == this._uid ||
                 service_url == this._canonical_url)
        {
            return this;
        }
        else
        {
            let func = "get_service";
            let args = {"service_uid": service_uid,
                        "service_url": service_url};

            try
            {
                let result = await this.call_function({func:func, args:args});
                let service = await Acquire.Service.from_data(
                                                result["service_info"]);
                return service;
            }
            catch(err)
            {
                throw new Acquire.ServiceError(
                    `Unable to get service because of failed function ` +
                    `call`, err);
            }
        }
    }

    async refresh_keys()
    {
        return;
    }

    async call_function({func=undefined, args=undefined})
    {
        if (this.is_null())
        {
            throw new Acquire.RemoteFunctionCallError(
                "You cannot call a function on a null service!");
        }

        if (this.should_refresh_keys())
        {
            await this.refresh_keys();
        }

        let response_key = Acquire.get_private_key("function");

        try
        {
            let result = await Acquire.call_function(
                                     {service_url:this.service_url(),
                                      func:func, args:args,
                                      args_key:this.public_key(),
                                      public_cert:this.public_certificate(),
                                      response_key:response_key});

            return result;
        }
        catch(err)
        {
            throw new Acquire.RemoteFunctionCallError(
                        `Error calling ${func} on ${this}`, err);
        }
    }

    async to_data()
    {
        let data = {};

        if (this.is_null()){ return data; }

        data["uid"] = this._uid;
        data["service_type"] = this._service_type;
        data["canonical_url"] = this._canonical_url;
        data["domain"] = this._domain;
        data["ports"] = this._ports;
        data["schemes"] = this._schemes;
        data["path"] = this._path;

        data["service_user_uid"] = this._service_user_uid;
        data["service_user_name"] = this._service_user_name;

        data["public_key"] = await this._pubkey.to_data();
        data["public_certificate"] = await this._pubcert.to_data();
        data["last_certificate"] = await this._lastcert.to_data();

        data["last_key_update"] = Acquire.datetime_to_string(
                                            this._last_key_update);
        data["key_update_interval"] = this._key_update_interval;

        return data;
    }

    static async from_data(data)
    {
        let service = new Acquire.Service();

        if (!data)
        {
            throw new Acquire.ServiceError(
                "Cannot construct a new Service from empty data!");
        }

        try
        {
            service._uid = data["uid"];
            service._service_type = data["service_type"];
            service._canonical_url = data["canonical_url"];
            service._domain = data["domain"];
            service._ports = data["ports"];
            service._schemes = data["schemes"];
            service._path = data["path"];

            service._service_user_uid = data["service_user_uid"];
            service._service_user_name = data["service_user_name"];

            service._pubkey = await Acquire.PublicKey.from_data(
                                                        data["public_key"])

            service._pubcert = await Acquire.PublicKey.from_data(
                                            data["public_certificate"], true)
            service._lastcert = await Acquire.PublicKey.from_data(
                                            data["last_certificate"], true);

            service._last_key_update = Acquire.string_to_datetime(
                                            data["last_key_update"])
            service._key_update_interval = parseFloat(
                                            data["key_update_interval"])
        }
        catch(err)
        {
            throw new Acquire.ServiceError(
                `Cannot construct service from ${data}`, err);
        }

        return service;
    }
 }
