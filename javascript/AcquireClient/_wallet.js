
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
}