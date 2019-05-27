

Acquire.Credentials = class {
    constructor({username=undefined, short_uid=undefined,
                 device_uid=undefined, password=undefined,
                 otpcode=undefined})
    {
        this._username = username;

        if (username)
        {
            this._short_uid = short_uid;
            this._device_uid = device_uid;
            this._password = password;
            this._otpcode = otpcode;
        }
    }

    is_null()
    {
        return (!this._username);
    }

    username()
    {
        if (this.is_null())
        {
            return undefined;
        }
        else
        {
            return this._username;
        }
    }

    short_uid()
    {
        if (this.is_null())
        {
            return undefined;
        }
        else
        {
            this._short_uid;
        }
    }

    device_uid()
    {
        if (this.is_null())
        {
            return undefined;
        }
        else
        {
            this._device_uid;
        }
    }

    password()
    {
        if (this.is_null())
        {
            return undefined;
        }
        else
        {
            return this._password;
        }
    }

    otpcode()
    {
        if (this.is_null())
        {
            return undefined;
        }
        else
        {
            return this._otpcode;
        }
    }

    async to_data({identity_uid=undefined})
    {
        if (this.is_null())
        {
            return undefined;
        }

        return await Acquire.Credentials.package(
                                         {identity_uid:identity_uid,
                                          short_uid:this._short_uid,
                                          username:this._username,
                                          password:this._password,
                                          otpcode:this._otpcode,
                                          device_uid:this._device_uid});
    }


    static async from_data(data, username, short_uid, random_sleep=150)
    {
        let result = await Acquire.Credentials.unpackage(
                                                 {data:data,
                                                  username:username,
                                                  short_uid:short_uid,
                                                  random_sleep:random_sleep});

        return new Acquire.Credentials(
                               {username:result["username"],
                                short_uid:result["short_uid"],
                                device_uid:result["device_uid"],
                                password:result["password"],
                                otpcode:result["otpcode"]});
    }

    assert_matching_username(username)
    {
        if (this.is_null() | this._username != username)
        {
            throw new Acquire.PermissionError(
                "Disagreement for the username for the matched credentials");
        }
    }

    static encode_device_uid({encoded_password, device_uid})
    {
        if (!(device_uid) | (!encoded_password))
        {
            return encoded_password;
        }

        let result = md5(encoded_password + device_uid);
        return result;
    }

    static encode_password({password, identity_uid, device_uid=undefined})
    {
        let encoded_password = Acquire.multi_md5(identity_uid, password);

        encoded_password = Acquire.Credentials.encode_device_uid(
                                        {encoded_password:encoded_password,
                                         device_uid:device_uid});

        return encoded_password;
    }

    static async package({identity_uid=undefined, short_uid=undefined,
                          username=undefined, password=undefined,
                          otpcode=undefined, device_uid=undefined})
    {
        if ((!username) | (!password) | (!otpcode))
        {
            throw new Acquire.PermissionError(
                "You must supply a username, password and otpcode " +
                "to be able to log in!");
        }

        let encoded_password = Acquire.Credentials.encode_password(
                                            {identity_uid:identity_uid,
                                             device_uid:device_uid,
                                             password:password});

        // if the device_uid is not set, then create a random one
        // so that an attacker does not know...
        if (!device_uid)
        {
            device_uid = Acquire.create_uuid();
        }

        let data = [encoded_password, device_uid, otpcode];
        let string_data = data.join("|");

        let uname_shortid = md5(username) + md5(short_uid);

        let symkey = new Acquire.SymmetricKey({symmetric_key:uname_shortid});
        string_data = await symkey.encrypt(string_data);

        return Acquire.bytes_to_string(string_data);
    }

    static async unpackage({data, username, short_uid, random_sleep=150})
    {
        let uname_shortid = md5(username) + md5(short_uid);
        data = string_to_bytes(data);

        let symkey = new Acquire.SymmetricKey({symmetric_key:uname_shortid});

        try
        {
            data = symkey.decrypt(data);
        }
        catch(_err)
        {
            data = undefined;
        }

        if (!data)
        {
            throw new Acquire.PermissionError(
                "Cannot unpackage/decrypt the credentials");
        }

        data = data.split("|");

        if (data.length < 3)
        {
            throw new Acquire.PermissionError(`Invalid credentials! ${data}`);
        }

        let result = {"username": username,
                      "short_uid": short_uid,
                      "device_uid": data[1],
                      "password": data[0],
                      "otpcode": data[2]};

        return result;
    }
}
