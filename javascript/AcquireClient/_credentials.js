

class Credentials
{
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

        return await Credentials.package({identity_uid:identity_uid,
                                          short_uid:this._short_uid,
                                          username:this._username,
                                          password:this._password,
                                          otpcode:this._otpcode,
                                          device_uid:this._device_uid});
    }


    static async from_data(data, username, short_uid, random_sleep=150)
    {
        var result = await Credentials.unpackage({data:data,
                                                  username:username,
                                                  short_uid:short_uid,
                                                  random_sleep:random_sleep});

        return new Credentials({username:result["username"],
                                short_uid:result["short_uid"],
                                device_uid:result["device_uid"],
                                password:result["password"],
                                otpcode:result["otpcode"]});
    }

    assert_matching_username(username)
    {
        if (this.is_null() | this._username != username)
        {
            throw new PermissionError(
                "Disagreement for the username for the matched credentials");
        }
    }

    static encode_device_uid({encoded_password, device_uid})
    {
        if (!(device_uid) | (!encoded_password))
        {
            return encoded_password;
        }

        var result = md5(encoded_password + device_uid);
        return result;
    }

    static encode_password({password, identity_uid, device_uid=undefined})
    {
        var encoded_password = multi_md5(identity_uid, password);

        console.log(`encoded_password = ${encoded_password}`);

        encoded_password = Credentials.encode_device_uid(
                                        {encoded_password:encoded_password,
                                         device_uid:device_uid});

        console.log(`with device_uid = ${encoded_password}`);

        return encoded_password;
    }

    static async package({identity_uid=undefined, short_uid=undefined,
                          username=undefined, password=undefined,
                          otpcode=undefined, device_uid=undefined})
    {
        if ((!username) | (!password) | (!otpcode))
        {
            throw new PermissionError(
                "You must supply a username, password and otpcode " +
                "to be able to log in!");
        }

        var encoded_password = Credentials.encode_password(
                                            {identity_uid:identity_uid,
                                             device_uid:device_uid,
                                             password:password});

        console.log(`identity_uid = ${identity_uid}`);
        console.log(`device_uid = ${device_uid}`);
        console.log(`password = ${password}`);
        console.log(`encoded_password = ${encoded_password}`);

        // if the device_uid is not set, then create a random one
        // so that an attacker does not know...
        if (!device_uid)
        {
            device_uid = create_uuid();
        }

        var data = [encoded_password, device_uid, otpcode];
        var string_data = data.join("|");

        console.log(`string_data = ${string_data}`);

        var uname_shortid = md5(username) + md5(short_uid);

        console.log(`uname_shortid = ${uname_shortid}`);

        var symkey = new SymmetricKey({symmetric_key:uname_shortid});
        string_data = await symkey.encrypt(string_data);
        var result = bytes_to_string(data);

        console.log(`string_data = ${result}`);

        return result;
    }

    static async unpackage({data, username, short_uid, random_sleep=150})
    {
        var uname_shortid = md5(username) + md5(short_uid);
        data = string_to_bytes(data);

        var symkey = new SymmetricKey({symmetric_key:uname_shortid});

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
            throw new PermissionError(
                "Cannot unpackage/decrypt the credentials");
        }

        data = data.split("|");

        if (data.length < 3)
        {
            throw new PermissionError(`Invalid credentials! ${data}`);
        }

        var result = {"username": username,
                      "short_uid": short_uid,
                      "device_uid": data[1],
                      "password": data[0],
                      "otpcode": data[2]};

        return result;
    }
}
