

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

    async to_data(identity_uid)
    {
        if (this.is_null())
        {
            return undefined;
        }

        return await Credentials.package({identity_uid:identity_uid,
                                          short_uid=this._short_uid,
                                          username=this._username,
                                          password=this._password,
                                          otpcode=this._otpcode,
                                          device_uid=this._device_uid});
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

        var result = Hash.md5(encoded_password + device_uid);
        return result;
    }

    static encode_password({password, identity_uid, device_uid=undefined})
    {
        var encoded_password = Hash.multi_md5(identity_uid, password);

        encoded_password = Credentials.encode_device_uid(
                                        {encoded_password:encoded_password,
                                         device_uid:device_uid});

        return encoded_password;
    }

    static async package({identity_uid, short_uid, username,
                          password, otpcode, device_uid=undefined})
    {
        if ((!username) | (!password) | (!otpcode))
        {
            throw new PermissionError(
                "You must supply a username, password and otpcode " +
                "to be able to log in!");
        }

        var encoded_password = Credentials.encode_password(
                                            identity_uid=identity_uid,
                                            device_uid=device_uid,
                                            password=password)

        # if the device_uid is not set, then create a random one
        # so that an attacker does not know...
        if device_uid is None:
            from Acquire.ObjectStore import create_uuid as _create_uuid
            device_uid = _create_uuid()

        data = [encoded_password, device_uid, otpcode]
        string_data = "|".join(data)

        uname_shortid = _Hash.md5(username) + _Hash.md5(short_uid)

        data = _SymmetricKey(symmetric_key=uname_shortid).encrypt(string_data)
        result = _bytes_to_string(data)
        return result

    @staticmethod
    def unpackage(data, username, short_uid, random_sleep=150):
        """Unpackage the credentials data packaged using "package" above,
        assuming that this data was packaged for the user login
        name "username" and for the session with short UID "short_uid".

        This will return a dictionary containing:

        username: Login name of the user
        short_uid: Short UID of the login session
        device_uid: UID of the login device (this will be random if it
                    was not set by the user)
        password: The MD5 of the password, salted using the UID of the
                    identity service, and optionally the device_uid
        otpcode: The one-time-password code for this login

        To make timing-based attacks harder, you can set 'random_sleep'
        to add an additional random sleep of up to 'random_sleep'
        milliseconds onto the end of the unpackage function

        Args:
                data (str): String of data containing credentials
                username (str): Username for session
                short_uid (str): UID for session
                random_sleep (int, default=150): Integer used to
                generate a random sleep to prevent timing attacks
        Returns:
                dict: Dictionary containing credentials

        """
        from Acquire.Crypto import Hash as _Hash
        from Acquire.Crypto import SymmetricKey as _SymmetricKey
        from Acquire.ObjectStore import string_to_bytes as _string_to_bytes
        from Acquire.ObjectStore import bytes_to_string as _bytes_to_string

        uname_shortid = _Hash.md5(username) + _Hash.md5(short_uid)

        data = _string_to_bytes(data)

        try:
            data = _SymmetricKey(symmetric_key=uname_shortid).decrypt(data)
        except:
            data = None

        if data is None:
            raise PermissionError("Cannot unpackage/decrypt the credentials")

        data = data.split("|")

        if len(data) < 3:
            raise PermissionError("Invalid credentials! %s" % data)

        result = {"username": username,
                "short_uid": short_uid,
                "device_uid": data[1],
                "password": data[0],
                "otpcode": data[2]}

        if random_sleep is not None:
            import random as _random
            import time as _time
            random_sleep = _random.randint(0, random_sleep)
            _time.sleep(0.001 * random_sleep)

        return result
