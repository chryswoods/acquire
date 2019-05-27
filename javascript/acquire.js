'use strict'

/** Holder for the Acquire "namespace" */
let Acquire = {};

/** "namespace" for all of the private Acquire classes/functions */
Acquire.Private = {};

/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

Acquire.login = async function ()
{
    try
    {
        let username = document.getElementById("username").value;
        let password = document.getElementById("password").value;
        let otpcode = document.getElementById("otpcode").value;
        let remember_device = document.getElementById("remember_device").value;
        let url = document.getElementById("url").value;

        let wallet = new Acquire.Wallet();
        await wallet.send_password({url:url, username:username,
                                    password:password, otpcode:otpcode,
                                    remember_device: remember_device});

        console.log("LOGIN SUCCESS!");
    }
    catch(err)
    {
        console.log(`LOGIN FAILED: ${err}`);
        console.log(err);
        let obj = JSON.parse(JSON.stringify(err));
        console.log(obj);
    }
}

Acquire.test_acquire = async function()
{
    try
    {
        let wallet = new Acquire.Wallet();

        wallet.clear();

        let service = await wallet.get_service({service_uid:"a0-a0"});

        console.log(service);

        service = await wallet.get_service(
                                {service_url:service.canonical_url()});

        console.log(service);

        let id_service = await wallet.get_service({service_uid:"a0-a1"});

        console.log(id_service);

        let user = new Acquire.User({username:"chryswoods"});

        console.log(user);

        let result = await user.request_login();

        console.log(user);

        console.log(result);
    }
    catch(err)
    {
        console.log(`UNCAUGHT EXCEPTION`);
        console.log(err);
        let obj = JSON.parse(JSON.stringify(err));
        console.log(obj);
    }
}


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

/** Return the current datetime (UTC) */
Acquire.get_datetime_now = function()
{
    return Acquire.datetime_to_datetime(new Date());
}

/** Return the current datetime (UTC) as a iso-formatted string
 *  that is suitable for Acquire
 */
Acquire.get_datetime_now_to_string = function()
{
    return Acquire.datetime_to_string(new Date());
}

/** Standardise the passed datetime into UTC */
Acquire.datetime_to_datetime = function(d)
{
    let date = new Date(d);
    let now_utc =  Date.UTC(date.getUTCFullYear(), date.getUTCMonth(),
                            date.getUTCDate(), date.getUTCHours(),
                            date.getUTCMinutes(), date.getUTCSeconds());

    return new Date(now_utc);
}

/** Convert the passed datetime into a standard formatted string */
Acquire.datetime_to_string = function(d)
{
    d = Acquire.datetime_to_datetime(d);
    d = d.toISOString();

    if (d.endsWith("Z"))
    {
        d = d.substr(0, d.length-1);
    }

    return d;
}

/** Convert the passed string back into a datetime */
Acquire.string_to_datetime = function(s)
{
    return Acquire.datetime_to_datetime(Date.parse(s));
}

/** Function to convert from a string back to binary */
Acquire.string_to_bytes = function(s)
{
    return base64js.toByteArray(s);
}

/** Function to convert binary data to a string */
Acquire.bytes_to_string = function(b)
{
    return base64js.fromByteArray(b);
}

/** Convert the passed string to a utf-8 array of bytes */
Acquire.string_to_utf8_bytes = function(s)
{
    return new TextEncoder("utf-8").encode(s);
}

/** Convert the passed array of utf-8 encoded bytes into a string  */
Acquire.utf8_bytes_to_string = function(b)
{
    return new TextDecoder("utf-8").decode(b);
}

/** Function to create url-safe strings */
Acquire.string_to_safestring = function(s)
{
    return Acquire.bytes_to_string(Acquire.string_to_utf8_bytes(s));
}

/** Function to return the original encoded string */
Acquire.safestring_to_string = function(s)
{
    return Acquire.utf8_bytes_to_string(Acquire.string_to_bytes(s));
}

/** Return the passed unicode string encoded to a safely
 *  encoded base64 utf-8 string
*/
Acquire.string_to_encoded = function(s)
{
    return Acquire.bytes_to_string(Acquire.string_to_utf8_bytes(s));
}

/** Return the passed encoded base64 utf-8 string converted
 *  back into a unicode string
 */
Acquire.encoded_to_string = function(b)
{
    return Acquire.utf8_bytes_to_string(Acquire.string_to_bytes(b));
}

/** Mirror of create_uuid
 *  Copied from
 *  https://stackoverflow.com/questions/105034/
 *                          create-guid-uuid-in-javascript
*/
Acquire.create_uuid = function()
{
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4)
                                                                .toString(16)
    )
}

Acquire.RemoteFunctionCallError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "RemoteFunctionCallError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.PermissionError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "PermissionError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.EncryptionError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "EncryptionError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.DecryptionError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "DecryptionError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.KeyManipulationError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "KeyManipulationError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.LoginError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "LoginError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.ServiceError = class extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "ServiceError";
        this.details = message;
        this.cause = cause;
    }
}

Acquire.unpack_arguments = async function(
                                {args=undefined, key=undefined,
                                 public_cert=undefined,
                                 is_return_value=false,
                                 func=undefined, service=undefined})
{
    let data = await args;

    if (data == undefined)
    {
        data = {};
    }

    let payload = undefined;

    if ("payload" in data)
    {
        payload = data["payload"];

        if ("exception" in payload)
        {
            throw new Acquire.RemoteFunctionCallError(
                "Error calling remote function", payload["exception"]);
        }
        else if ("error" in payload)
        {
            throw new Acquire.RemoteFunctionCallError(
                    "Error calling remote function", payload["error"]);
        }
        else if ("status" in payload)
        {
            if (payload["status"] != 0)
            {
                throw new Acquire.RemoteFunctionCallError(
                    "Error calling remote function", payload);
            }
        }
    }

    let is_encrypted = ("encrypted" in data);
    let signature = undefined;

    if (public_cert != undefined)
    {
        if (!is_encrypted)
        {
            throw new Acquire.RemoteFunctionCallError(
                "Cannot unpack result as should be signed, but isn't. " +
                "Only encrypted results can be signed");
        }

        if (!("signature" in data))
        {
            throw new Acquire.RemoteFunctionCallError(
                "We requested the data was signed, but no signature found!");
        }

        signature = Acquire.string_to_bytes(data["signature"]);
    }

    if (is_encrypted)
    {
        let encrypted_data = Acquire.string_to_bytes(data["data"]);

        if (signature != undefined)
        {
            await public_cert.verify(signature, encrypted_data);
        }

        let fingerprint = data["fingerprint"];

        let my_fingerprint = await key.fingerprint();

        if (fingerprint != my_fingerprint)
        {
            throw new Acquire.RemoteFunctionCallError(
                "Cannot decrypt result - conflicting fingerprints " +
                `${fingerprint} versus ${my_fingerprint}`);
        }

        let decrypted_data = await key.decrypt(encrypted_data);
        decrypted_data = JSON.parse(decrypted_data);

        return await Acquire.unpack_arguments(
                                      {args:decrypted_data,
                                       is_return_value:is_return_value,
                                       func:func, service:service});
    }

    if (payload == undefined)
    {
        throw new Acquire.RemoteFunctionCallError(
            "Strange - no payload by this point in the call?");
    }

    return payload["return"];
}

Acquire.unpack_return_value = async function(
                                   {return_value=undefined,
                                    key=undefined, public_cert=undefined,
                                    func=undefined, service=undefined})
{
    return await Acquire.unpack_arguments(
                                  {args:return_value,
                                   key:key, public_cert:public_cert,
                                   is_return_value:true,
                                   func:func, service:service});
}

Acquire.pack_return_value = async function(
                                 {func=undefined, payload=undefined,
                                  key=undefined, response_key=undefined,
                                  public_cert=undefined,
                                  private_cert=undefined})
{
    if (func == undefined)
    {
        func = payload["function"];
    }

    let result = {};

    let now = Acquire.get_datetime_now_to_string();

    result["function"] = func;
    result["payload"] = payload;
    result["synctime"] = now;

    if (response_key != undefined)
    {
        let bytes = await response_key.bytes();
        bytes = Acquire.string_to_utf8_bytes(bytes);
        bytes = Acquire.bytes_to_string(bytes);
        result["encryption_public_key"] = bytes;

        if (public_cert != undefined)
        {
            let fingerprint = await public_cert.fingerprint();
            result["sign_with_service_key"] = fingerprint;
        }
    }

    let result_json = JSON.stringify(result);

    if (key != undefined)
    {
        // encrypt what we send to the server
        let result_data = await key.encrypt(result_json);
        let fingerprint = await key.fingerprint();

        result = {};
        result["data"] = Acquire.bytes_to_string(result_data);
        result["encrypted"] = true;
        result["fingerprint"] = fingerprint;
        result["synctime"] = now;
        result_json = JSON.stringify(result);
    }

    return result_json;
}

Acquire.pack_arguments = async function(
                              {func=undefined, args=undefined,
                               key=undefined, response_key=undefined,
                               public_cert=undefined})
{
    return await Acquire.pack_return_value(
                                   {func:func, payload:args,
                                    key:key, response_key:response_key,
                                    public_cert:public_cert});
}

/** Call the specified URL */
Acquire.call_function = async function(
                             {service_url=undefined, func=undefined,
                              args=undefined, args_key=undefined,
                              response_key=undefined, public_cert=undefined})
{
    if (args == undefined)
    {
        args = {};
    }

    var args_json = undefined;

    if (response_key == undefined)
    {
        args_json = await Acquire.pack_arguments(
                                    {func:func, args:args, key:args_key});
    }
    else
    {
        var pubkey = await response_key.public_key();
        args_json = await Acquire.pack_arguments(
                                         {func:func, args:args, key:args_key,
                                          response_key:pubkey,
                                          public_cert:public_cert});
    }

    var response = null;

    try
    {
        response = await fetch(service_url,
                        {method: 'post',
                         headers: {
                            'Accept': 'application/json, test/plain, */*',
                            'Content-Type': 'application/json'
                         },
                         body: args_json});

        response = await response.json();
    }
    catch(err)
    {
        throw new Acquire.RemoteFunctionCallError(
            `Error calling function ${service_url}`, err);
    }

    var result = undefined;

    try
    {
        result = JSON.parse(response);
    }
    catch(err)
    {
        throw new Acquire.RemoteFunctionCallError(
            `Error extracting json from function ${service_url}`, err);
    }

    try
    {
        result = await Acquire.unpack_return_value(
                            {return_value:result, key:response_key,
                             public_cert:public_cert, func:func,
                             service:service_url});
    }
    catch(err)
    {
        throw new Acquire.RemoteFunctionCallError(
            `Error upacking result from function ${service_url}`, err);
    }

    return result;
}

/** Mirror of Acquire.Crypto.Hash.multi_md5 */
Acquire.multi_md5 = function(data1, data2)
{
    return md5(md5(data1) + md5(data2));
}

/** Function used as part of converting a key to a pem file */
Acquire.Private._arrayBufferToBase64String = function(arrayBuffer)
{
    let byteArray = new Uint8Array(arrayBuffer)
    let byteString = ''
    for (let i=0; i<byteArray.byteLength; i++) {
        byteString += String.fromCharCode(byteArray[i])
    }
    return btoa(byteString)
}

/** Function to convert a base64 string to an array buffer */
Acquire.Private._base64StringToArrayBuffer = function(b64str)
{
    let byteStr = atob(b64str)
    let bytes = new Uint8Array(byteStr.length)
    for (let i = 0; i < byteStr.length; i++) {
        bytes[i] = byteStr.charCodeAt(i)
    }
    return bytes.buffer
}

/** Function used to convert binary key date to pem */
Acquire.Private._convertBinaryToPem = function(binaryData, label) {
    let base64Cert = Acquire.Private._arrayBufferToBase64String(binaryData)
    let pemCert = "-----BEGIN " + label + "-----\n"
    let nextIndex = 0
    let lineLength
    while (nextIndex < base64Cert.length) {
        if (nextIndex + 64 <= base64Cert.length) {
        pemCert += base64Cert.substr(nextIndex, 64) + "\n"
        } else {
        pemCert += base64Cert.substr(nextIndex) + "\n"
        }
        nextIndex += 64
    }
    pemCert += "-----END " + label + "-----\n"
    return pemCert
}

/** Function to convert pemfile info binary data used for js crypto */
Acquire.Private._convertPemToBinary = function(pem)
{
    let lines = pem.split('\n')
    let encoded = ''
    for(let i = 0;i < lines.length;i++){
        if (lines[i].trim().length > 0 &&
            lines[i].indexOf('-BEGIN PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-BEGIN ENCRYPTED PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-BEGIN PUBLIC KEY-') < 0 &&
            lines[i].indexOf('-END PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-END ENCRYPTED PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-END PUBLIC KEY-') < 0) {
        encoded += lines[i].trim()
        }
    }
    return Acquire.Private._base64StringToArrayBuffer(encoded)
}

/** Hard code the key size (in bytes) as javascript web crypto doesn't
 *  seem to have a way to query this programatically. 256 bytes (2048 bit)
 *  is used on the server in all of the python functions
*/
Acquire.Private._rsa_key_size = 256;

/** Funcion to import and return the public key from the passed pemfile */
Acquire.Private._importPublicKey = async function(pemKey)
{
    //convert the pem key to binary
    let bin = Acquire.Private._convertPemToBinary(pemKey);

    let encryptAlgorithm = {
        name: "RSA-OAEP",
        modulusLength: 8*Acquire.Private._rsa_key_size,
        publicExponent: 65537,
        extractable: true,
        hash: {
            name: "SHA-256"
        }
    };

    try
    {
        let public_key = await crypto.subtle.importKey(
                            "spki", bin, encryptAlgorithm,
                            true, ["encrypt"]
                            );

        return public_key;
    }
    catch(err)
    {
        throw new Acquire.KeyManipulationError(
            "Cannot import public key!", err);
    }
}


/** Function to import and return the public cert from the passed pemfile */
Acquire.Private._importPublicCert = async function(pemKey)
{
    //convert the pem key to binary
    let bin = Acquire.Private._convertPemToBinary(pemKey);

    let encryptAlgorithm = {
        name: "RSA-OAEP",
        modulusLength: 8*Acquire.Private._rsa_key_size,
        publicExponent: 65537,
        extractable: true,
        hash: {
            name: "SHA-256"
        }
    };

    try
    {
        let public_key = await crypto.subtle.importKey(
                            "spki", bin, encryptAlgorithm,
                            true, ["encrypt"]
                            );

        return public_key;
    }
    catch(err)
    {
        throw new Acquire.KeyManipulationError(
            "Cannot import public certificate!", err);
    }
}

/** Function to convert a public key to a PEM file */
Acquire.Private._exportPublicKey = async function(key) {
    let exported = await window.crypto.subtle.exportKey('spki', key);
    let pem = Acquire.Private._convertBinaryToPem(exported, "PUBLIC KEY");
    return pem;
}

/** Function to import and return the private key from the passed pemfile.
 *  Note that this doesn't, yet, work with encrypted pem files
 */
Acquire.Private._importPrivateKey = async function(pemKey, passphrase)
{
    //convert the pem key to binary
    let bin = Acquire.Private._convertPemToBinary(pemKey);

    let encryptAlgorithm = {
        name: "RSA-OAEP",
        modulusLength: 8*Acquire.Private._rsa_key_size,
        publicExponent: 65537,
        extractable: true,
        hash: {
            name: "SHA-256"
        }
    };

    try
    {
        let private_key = await crypto.subtle.importKey(
                            "spki", bin, encryptAlgorithm,
                            true, ["encrypt", "decrypt", "sign", "verify"]
                            );

        return private_key;
    }
    catch(err)
    {
        throw new Acquire.KeyManipulationError(
            "Cannot import private key", err);
    }
}

/** Function to convert a private key to a PEM file. Currently
 *  this does not encrypt the PEM file. It will one day, when
 *  if will use the supplied passphrase
 */
Acquire.Private._exportPrivateKey = async function(key, passphrase) {
    let exported = await window.crypto.subtle.exportKey('spki', key);
    let pem = Acquire.Private._convertBinaryToPem(exported, "PRIVATE KEY");
    return pem;
}

/** Function that concatenates two arrays together -
 *  thanks to http://2ality.com/2015/10/concatenating-typed-arrays.html
 */
Acquire.Private._concatenate = function(resultConstructor, ...arrays)
{
    let totalLength = 0;
    for (let arr of arrays)
    {
        totalLength += arr.length;
    }

    let result = new resultConstructor(totalLength);
    let offset = 0;
    for (let arr of arrays)
    {
        result.set(arr, offset);
        offset += arr.length;
    }
    return result;
}

/*
Thanks to Jon Leighton for the below base64ArrayBuffer function that is
  licensed under MIT

MIT LICENSE
Copyright 2011 Jon Leighton
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
*/
Acquire.Private._base64ArrayBuffer = function(arrayBuffer)
{
    let base64    = '';
    let encodings = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

    let bytes         = new Uint8Array(arrayBuffer);
    let byteLength    = bytes.byteLength;
    let byteRemainder = byteLength % 3;
    let mainLength    = byteLength - byteRemainder;

    let a, b, c, d = undefined;
    let chunk = undefined;

    // Main loop deals with bytes in chunks of 3
    for (let i = 0; i < mainLength; i = i + 3) {
      // Combine the three bytes into a single integer
      chunk = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2];

      // Use bitmasks to extract 6-bit segments from the triplet
      a = (chunk & 16515072) >> 18; // 16515072 = (2^6 - 1) << 18
      b = (chunk & 258048)   >> 12; // 258048   = (2^6 - 1) << 12
      c = (chunk & 4032)     >>  6; // 4032     = (2^6 - 1) << 6
      d = chunk & 63;               // 63       = 2^6 - 1

      // Convert the raw binary segments to the appropriate ASCII encoding
      base64 += encodings[a] + encodings[b] + encodings[c] + encodings[d];
    }

    // Deal with the remaining bytes and padding
    if (byteRemainder == 1) {
      chunk = bytes[mainLength];

      a = (chunk & 252) >> 2; // 252 = (2^6 - 1) << 2

      // Set the 4 least significant bits to zero
      b = (chunk & 3)   << 4; // 3   = 2^2 - 1

      base64 += encodings[a] + encodings[b] + '==';
    } else if (byteRemainder == 2) {
      chunk = (bytes[mainLength] << 8) | bytes[mainLength + 1];

      a = (chunk & 64512) >> 10; // 64512 = (2^6 - 1) << 10
      b = (chunk & 1008)  >>  4; // 1008  = (2^6 - 1) << 4

      // Set the 2 least significant bits to zero
      c = (chunk & 15)    <<  2; // 15    = 2^4 - 1

      base64 += encodings[a] + encodings[b] + encodings[c] + '=';
    }

    return base64;
}

/** Function to perform symmetric encryption using fernet - encrypts
 *  'data' with 'key'
 */
Acquire.Private.fernet_encrypt = function(key, data)
{
    let token = new fernet.Token({
        secret: new fernet.Secret(key)
    });

    try
    {
        let encrypted = token.encode(data);
        encrypted = Acquire.string_to_utf8_bytes(encrypted);
        return encrypted;
    }
    catch(err)
    {
        throw new Acquire.EncryptionError("Cannot encrypt data", err);
    }
}

/** Function to perform symmetric decryption using fernet - decrypts
 *  'data' with 'key'
 */
Acquire.Private.fernet_decrypt = function(key, data)
{
    let token = new fernet.Token({
        secret: new fernet.Secret(key),
        token: Acquire.utf8_bytes_to_string(data),
        ttl: 0
    });

    try
    {
        let result = token.decode();
        return result;
    }
    catch(err)
    {
        throw new Acquire.DecryptionError("Cannot decrypt data", err);
    }
}

/** Randomly generate a good symmetric key */
Acquire.Private._generate_symmetric_key = function()
{
    let array = new Uint8Array(32);
    window.crypto.getRandomValues(array);
    let secret = Acquire.Private._base64ArrayBuffer(array);
    return secret;
}

/** Function that verifies the signature of the passed message signed
 *  using the private counterpart of this public key
 */
Acquire.Private._verifySignature = async function(key, signature, data)
{
    key = await key;

    // this is something we will attempt at a much later point!
}

/** Function that encrypts the passed data with the passed public key */
Acquire.Private._encryptData = async function(key, data)
{
    try
    {
        key = await key;

        // we will encrypt the message using fernet, and send that prefixed
        // by the RSA-encrypted secret. The fernet secret is a random 32 bytes
        // that are then base64 encoded
        let array = new Uint8Array(32);
        window.crypto.getRandomValues(array);
        let secret = Acquire.Private._base64ArrayBuffer(array);

        let token = new fernet.Token({
            secret: new fernet.Secret(secret)
        });

        let encrypted = token.encode(data);

        // now we will encrypt the fernet secret using the public key
        let result = await window.crypto.subtle.encrypt(
                        {
                            name: "RSA-OAEP"
                        },
                        key,
                        Acquire.string_to_utf8_bytes(secret).buffer
                    );

        // finally concatenate both outputs together into a single binary array
        let output = new Uint8Array(result);
        output = Acquire.Private._concatenate(
                                    Uint8Array,
                                    output,
                                    Acquire.string_to_utf8_bytes(encrypted));

        return output;
    }
    catch(err)
    {
        throw new Acquire.EncryptionError(
            "Failed to encrypt the data!", err);
    }
}

/** Function that decrypts the passed data with the passed private key */
Acquire.Private._decryptData = async function(key, data)
{
    try
    {
        // the first rsa_key_size bytes hold the rsa-encrypted fernet
        // secret to decode the rest of the message
        let secret = await window.crypto.subtle.decrypt(
                    {
                        name: "RSA-OAEP",
                    },
                    key,
                    data.slice(0,Acquire.Private._rsa_key_size))
                ;

        secret = Acquire.utf8_bytes_to_string(secret);

        if (data.length <= Acquire.Private._rsa_key_size){
            // the secret is the message - no fernet decoding needed
            return secret;
        }

        data = Acquire.utf8_bytes_to_string(
                                    data.slice(Acquire.Private._rsa_key_size,
                                            data.length));

        let token = new fernet.Token({
            secret: new fernet.Secret(secret),
            token: data,
            ttl: 0
        });

        let result = token.decode();

        return result;
    }
    catch(err)
    {
        throw new Acquire.DecryptionError("Cannot decrypt data", err);
    }
}

/** Function to generate a public/private key pair used for
 *  encrypting and decrypting
 */
Acquire.Private._generateKeypair = async function()
{
    try
    {
        let keys = await window.crypto.subtle.generateKey(
            {
                name: "RSA-OAEP",
                modulusLength: 8*Acquire.Private._rsa_key_size,
                publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
                hash: {name: "SHA-256"}
            },
            true,  /* the key must be extractable */
            ["encrypt", "decrypt"]
        );

        await keys;
        return keys;
    }
    catch(err)
    {
        throw new Acquire.KeyManipulationError("Unable to generate keys", err);
    }
}

/** Function to generate a public/private key pair used for
 *  signing and verifying
 */
Acquire.Private._generateCertpair = async function()
{
    try
    {
        let keys = await window.crypto.subtle.generateKey(
            {
                name: "RSA-OAEP",
                modulusLength: 8*Acquire.Private._rsa_key_size,
                publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
                hash: {name: "SHA-256"}
            },
            true,  /* the key must be extractable */
            ["sign", "verify"]
        );

        return keys;
    }
    catch(err)
    {
        throw new Acquire.KeyManipulationError("Unable to generate keys", err);
    }
}

/** This class provides a simple handle to a private key. This
 *  can be used to decrypt data for Acquire, and also to
 *  sign messages
 */
Acquire.PrivateKey = class
{
    constructor(auto_generate=true)
    {
        if (auto_generate)
        {
            this._keys = Acquire.Private._generateKeypair();
        }
        else
        {
            this._keys = undefined;
        }
    }

    is_null()
    {
        return this._keys == undefined;
    }

    async fingerprint()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            let key = await this.public_key();
            return await key.fingerprint();
        }
    }

    async public_key()
    {
        if (this.is_null()){ return undefined;}
        else
        {
            let keys = await this._keys;
            return new Acquire.PublicKey(keys.publicKey);
        }
    }

    async bytes(passphrase)
    {
        if (this.is_null()){ return undefined; }
        else
        {
            let keys = await this._keys;
            let pem = await Acquire.Private._exportPrivateKey(
                                                keys.privateKey, passphrase);
            return pem;
        }
    }

    async encrypt(message)
    {
        if (this.is_null()){ return undefined;}
        else
        {
            let pubkey = await this.public_key();
            return await pubkey.encrypt(message);
        }
    }

    async decrypt(message)
    {
        if (this.is_null()){ return undefined;}
        else
        {
            let keys = await this._keys;
            return await Acquire.Private._decryptData(keys.privateKey,
                                                      message);
        }
    }

    async to_data(passphrase)
    {
        if (this.is_null()){ return undefined; }
        else
        {
            let bytes = await this.bytes(passphrase);

            let data = {};
            data["bytes"] = Acquire.bytes_to_string(bytes);

            return data;
        }
    }

    static async read_bytes(bytes, passphrase)
    {
        let keys = await Acquire.Private._importPrivateKey(bytes,
                                                           passphrase);

        let privkey = new Acquire.PrivateKey(false);
        privkey._keys = keys;
        return privkey;
    }

    static async from_data(data, passphrase)
    {
        let pem = Acquire.string_to_bytes(data["bytes"]);
        pem = Acquire.utf8_bytes_to_string(pem);
        return await Acquire.PrivateKey.read_bytes(pem, passphrase);
    }
}

/** This class provides a simple handle to a public key. This
 *  can be used to encrypt data for Acquire and verify signatures
 */
Acquire.PublicKey = class
{
    constructor(public_key=undefined)
    {
        this._key = public_key;
    }

    is_null()
    {
        return this._key == undefined;
    }

    async bytes()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            let pem = await Acquire.Private._exportPublicKey(this._key);
            return pem;
        }
    }

    async fingerprint()
    {
        if (this.is_null()){ return undefined; }
        else
        {
            //the fingerprint is an md5 of the pem
            let b = await this.bytes();
            let m = md5(b);

            return m.match(/(..?)/g).join(":");
        }
    }

    async verify(signature, message)
    {
        if (this.is_null()){ return undefined; }
        else
        {
            await Acquire.Private._verifySignature(this._key,
                                                   signature, message);
        }
    }

    async encrypt(message)
    {
        return await Acquire.Private._encryptData(this._key, message);
    }

    async to_data()
    {
        if (this.is_null()){ return undefined; }

        let pem = await Acquire.Private._exportPublicKey(this._key);
        let b = Acquire.bytes_to_string(Acquire.string_to_utf8_bytes(pem));

        let data = {};
        data["bytes"] = b;

        return data;
    }

    static async from_data(data, is_certificate=false)
    {
        if (data == undefined){ return undefined;}

        let key = new Acquire.PublicKey();

        let b = data["bytes"];

        let pem = Acquire.string_to_bytes(data["bytes"]);
        pem = Acquire.utf8_bytes_to_string(pem);

        if (is_certificate)
        {
            key._key = await Acquire.Private._importPublicCert(pem);
        }
        else
        {
            key._key = await Acquire.Private._importPublicKey(pem);
        }

        return key;
    }
}

Acquire.SymmetricKey = class
{
    constructor({symmetric_key=undefined, auto_generate=true} = {})
    {
        this._symkey = undefined;

        if (symmetric_key)
        {
            this._symkey = Acquire.string_to_encoded(md5(symmetric_key));
        }
        else
        {
            if (auto_generate)
            {
                this._symkey = Acquire.Private._generate_symmetric_key();
            }
        }
    }

    fingerprint()
    {
        if (!self._symkey)
        {
            return undefined;
        }

        let m = md5(self._symkey);

        return m.match(/(..?)/g).join(":");
    }

    encrypt(message)
    {
        if (!this._symkey)
        {
            this._symkey = Acquire.Private._generate_symmetric_key();
        }

        return Acquire.Private.fernet_encrypt(this._symkey, message);
    }

    decrypt(message)
    {
        if (!this._symkey)
        {
            throw new Acquire.DecryptionError(
                                      "You cannot decrypt a message " +
                                      "with a null key!");
        }

        return Acquire.Private.fernet_decrypt(this._symkey, message);
    }
}

/** Keys for the root registry service */

let _a0_a0_public_key = {'bytes': 'LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUE1UWZXdnVPVFROeEJ2ZkhZak5FcwpzU3czMUxxUWhlN211UExheXgwT3N1YjJTVUxlZCtXTkRScUxROHpJQTc3bG1hNXArTGpDTVFUZnoxaTlSSVBmCnI0SDBxa3YxMmYzYVNiVjN0aFFUekNIekoxMi9lNDJTVi8wZnhOejB1azhIbUsrSk9zOHg3dm5BUWxxbEJDVmIKM0hqQ0pwUy9IUGJXaXZxM1RjaFlJbkltWXdjaU8rdXZvZzZuTEJOSHhHOUZBTTRMWFprcnBXWmhJa2doOUhZOQpGUjhiZkJhNmdvQmpmM3QwUVlNUHBpaWd6K0NSU2JDQ2xCVzV6SW1iWGhnUHJsQVZKY2w2c2l0T0xRQVVIUHNUCnlvQzU0VmpvNVZVeFhqYkpEbXZzTERiQnUzZ0xWOVd0MGVvMHpBdGlmR3R0WXdmRndFSThOTi84MnBlUXJQZ0gKQlFJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=='};
let _a0_a0_public_certificate = {'bytes': 'LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUExVmhwOGtqY3VyUWtmWDU3Q2NKZApWbkNlblNxWllMRmJoVCt0SVVMa0lTdG9EWjVVWFRub241aUJOdFEzWkxDbG5RVTdxZEFjMzlLSlh1QmZ1M3RzCk1iaUE5YUpUQURPcEFPclBiRFhTcHI2Q0J4WkRzczF3NkxodlpISmRzNW50OUQzUnVaaTQ5ZXlZZ0oxVVR3aHQKMkJXM2hRcWVoMVkxY294QU9YSWtlZUpvZnFvOWMzaE4wQ21ZVE5kKzRlZ1Rmd2tLUHovNEZaYnlHUVg3dmF2aApoelBXSWw5U0xuTDBIdDBHMUVvN3hzd1VEMHVUbk80VGdmcmdHWmZaNVU5cjNFa2xrMTg0KzdFZGRGVXphSlgwClF1TjROd0ErbGN5ZHNFRW5oaXpIVjNoUS84U2k2ZjZFNlM5djJQTU44anpYdFhtRFZ2VzNENjJ5SFVndmdXUzkKNHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=='};
let _a0_a0_service_url = "http://fn.acquire-aaai.com:8080/t/registry";

Acquire.root_server = {"a0-a0":
                        {"service_url": _a0_a0_service_url,
                         "public_key": _a0_a0_public_key,
                         "public_certificate": _a0_a0_public_certificate}};

/** Below function inspired by TOTP generator at
 * https://www.thepolyglotdeveloper.com/2014/10/generate-time-based-one-time-passwords-javascript/
 *
 * Adapted to use webcrypto hmac function
 */
Acquire.TOTP = function() {

    let dec2hex = function(s) {
        return (s < 15.5 ? "0" : "") + Math.round(s).toString(16);
    };

    let hex2dec = function(s) {
        return parseInt(s, 16);
    };

    let leftpad = function(s, l, p) {
        if(l + 1 >= s.length) {
            s = Array(l + 1 - s.length).join(p) + s;
        }
        return s;
    };

    let base32tohex = function(base32) {
        var base32chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        var bits = "";
        var hex = "";
        for(var i = 0; i < base32.length; i++) {
            var val = base32chars.indexOf(base32.charAt(i).toUpperCase());
            bits += leftpad(val.toString(2), 5, '0');
        }
        for(var i = 0; i + 4 <= bits.length; i+=4) {
            var chunk = bits.substr(i, 4);
            hex = hex + parseInt(chunk, 2).toString(16) ;
        }
        return hex;
    };

    this.getOTP = function(secret) {
        try {
            let epoch = Math.round(new Date().getTime() / 1000.0);
            let time = leftpad(dec2hex(Math.floor(epoch / 30)), 16, "0");
            let hmacObj = new jsSHA(time, "HEX");
            let hmac = hmacObj.getHMAC(base32tohex(secret), "HEX", "SHA-1", "HEX");
            let offset = hex2dec(hmac.substring(hmac.length - 1));
            let otp = (hex2dec(hmac.substr(offset * 2, 8)) & hex2dec("7fffffff")) + "";
            otp = (otp).substr(otp.length - 6, 6);
        } catch (error) {
            throw error;
        }
        return otp;
    };
}

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

Acquire.Private._get_identity_service = async function(
                                            {identity_url=undefined,
                                             identity_uid=undefined})
{
    if (!identity_url)
    {
        if (!identity_uid)
        {
            identity_uid = "a0-a1";
        }
    }

    let wallet = new Acquire.Wallet();
    let service = undefined;

    try
    {
        service = await wallet.get_service({service_url:identity_url,
                                            service_uid:identity_uid});
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

        if (identity_url)
        {
            this._identity_url = identity_url;
        }
        else
        {
            this._identity_url = undefined;
        }

        if (identity_uid)
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
            throw new Acquire.LoginError(this._error_string,
                                         this._error_exception);
        }
    }

    _set_error_state(message, error=undefined)
    {
        this._status = "ERROR";
        this._error_string = message;
        this._error_exception = error;
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
                                {identity_url:this._identity_url,
                                 identity_uid:this._identity_uid});
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
            return undefined;
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
            let error = "Could not complete login!";
            this._set_error_state(error, err);
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
            console.log("BOOTSTRAPPING REGISTRY");
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

        // now get the service
        let service = undefined;
        try
        {
            service = await this.get_service({service_uid:service_uid});
        }
        catch(err)
        {
            throw new Acquire.LoginError(
                `Cannot find the service with UID ${service_uid}`, err);
        }

        if (!service.can_identify_users())
        {
            throw new Acquire.LoginError(
                `Service ${service} is unable to identify users! ` +
                `You cannot log into something that is not a valid ` +
                `identity service!`);
        }

        let userinfo = await this._find_userinfo({username:username,
                                                  password:password});

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