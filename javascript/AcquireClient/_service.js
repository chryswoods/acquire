
class Service
{
    /** Construct a service that is accessed at 'service_url'.
     *  This will automatically connect to the service to obtain
     *  the necessary service information.
     *
     *  Args:
     *      service_url = URL of the service to connect to
     *      service_uid = UID of the service to connect to
     *      service_type = expected type of the service
     */
    constructor({service_url=undefined, service_uid=undefined,
                 service_type=undefined} = {})
    {
        this._canonical_url = service_url;
        this._uid = service_uid;
        this._service_type = service_type;
    }

    /** Return whether or not this is a null Service */
    is_null()
    {
        return this._uid == undefined;
    }

    /** Return the UID of this service */
    uid()
    {
        return this._uid;
    }

    /** Return the type of this Service */
    service_type()
    {
        if (this.is_null()){ return undefined; }
        else { return this._service_type; }
    }

    /** Return the UID of the registry that registered this service */
    registry_uid()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            var root = this.uid().split("-")[0];
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

    async to_data()
    {
        var data = {};

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

        data["last_key_update"] = datetime_to_string(this._last_key_update);
        data["key_update_interval"] = this._key_update_interval;

        return data;
    }

    static async from_data(data)
    {
        var service = new Service();

        service._uid = data["uid"];
        service._service_type = data["service_type"];
        service._canonical_url = data["canonical_url"];
        service._domain = data["domain"];
        service._ports = data["ports"];
        service._schemes = data["schemes"];
        service._path = data["path"];

        service._service_user_uid = data["service_user_uid"];
        service._service_user_name = data["service_user_name"];

        service._pubkey = await PublicKey.from_data(data["public_key"])
        service._pubcert = await PublicKey.from_data(
                                            data["public_certificate"])
        service._lastcert = await PublicKey.from_data(
                                            data["last_certificate"]);

        service._last_key_update = string_to_datetime(data["last_key_update"])
        service._key_update_interval = parseFloat(data["key_update_interval"])

        return service;
    }
 }
