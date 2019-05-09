

/** Function used as part of converting a key to a pem file */
function _arrayBufferToBase64String(arrayBuffer)
{
    var byteArray = new Uint8Array(arrayBuffer)
    var byteString = ''
    for (var i=0; i<byteArray.byteLength; i++) {
        byteString += String.fromCharCode(byteArray[i])
    }
    return btoa(byteString)
}

/** Function to convert a base64 string to an array buffer */
function _base64StringToArrayBuffer(b64str)
{
    var byteStr = atob(b64str)
    var bytes = new Uint8Array(byteStr.length)
    for (var i = 0; i < byteStr.length; i++) {
        bytes[i] = byteStr.charCodeAt(i)
    }
    return bytes.buffer
}

/** Function used to convert binary key date to pem */
function _convertBinaryToPem(binaryData, label) {
    var base64Cert = _arrayBufferToBase64String(binaryData)
    var pemCert = "-----BEGIN " + label + "-----\n"
    var nextIndex = 0
    var lineLength
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
function _convertPemToBinary(pem)
{
    var lines = pem.split('\n')
    var encoded = ''
    for(var i = 0;i < lines.length;i++){
        if (lines[i].trim().length > 0 &&
            lines[i].indexOf('-BEGIN PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-BEGIN PUBLIC KEY-') < 0 &&
            lines[i].indexOf('-END PRIVATE KEY-') < 0 &&
            lines[i].indexOf('-END PUBLIC KEY-') < 0) {
        encoded += lines[i].trim()
        }
    }
    return _base64StringToArrayBuffer(encoded)
}

/** Hard code the key size (in bytes) as javascript web crypto doesn't
 *  seem to have a way to query this programatically. 256 bytes (2048 bit)
 *  is used on the server in all of the python functions
*/
var _rsa_key_size = 256;

/** Function to import and return the public key from the passed pemfile */
async function _importPublicKey(pemKey)
{
    //convert the pem key to binary
    var bin = _convertPemToBinary(pemKey);

    var encryptAlgorithm = {
        name: "RSA-OAEP",
        modulusLength: 8*_rsa_key_size,
        publicExponent: 65537,
        extractable: false,
        hash: {
            name: "SHA-256"
        }
    };

    var public_key = await crypto.subtle.importKey(
                        "spki", bin, encryptAlgorithm,
                        true, ["encrypt"]
                        );

    return public_key;
}

/** Function to convert a public key to a PEM file */
async function _exportPublicKey(key) {
    let exported = await window.crypto.subtle.exportKey('spki', key);
    let pem = _convertBinaryToPem(exported, "PUBLIC KEY");
    return pem;
}

/** Function that concatenates two arrays together -
 *  thanks to http://2ality.com/2015/10/concatenating-typed-arrays.html
 */
function _concatenate(resultConstructor, ...arrays)
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
function _base64ArrayBuffer(arrayBuffer)
{
    var base64    = ''
    var encodings = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    var bytes         = new Uint8Array(arrayBuffer)
    var byteLength    = bytes.byteLength
    var byteRemainder = byteLength % 3
    var mainLength    = byteLength - byteRemainder

    var a, b, c, d
    var chunk

    // Main loop deals with bytes in chunks of 3
    for (var i = 0; i < mainLength; i = i + 3) {
      // Combine the three bytes into a single integer
      chunk = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2]

      // Use bitmasks to extract 6-bit segments from the triplet
      a = (chunk & 16515072) >> 18 // 16515072 = (2^6 - 1) << 18
      b = (chunk & 258048)   >> 12 // 258048   = (2^6 - 1) << 12
      c = (chunk & 4032)     >>  6 // 4032     = (2^6 - 1) << 6
      d = chunk & 63               // 63       = 2^6 - 1

      // Convert the raw binary segments to the appropriate ASCII encoding
      base64 += encodings[a] + encodings[b] + encodings[c] + encodings[d]
    }

    // Deal with the remaining bytes and padding
    if (byteRemainder == 1) {
      chunk = bytes[mainLength]

      a = (chunk & 252) >> 2 // 252 = (2^6 - 1) << 2

      // Set the 4 least significant bits to zero
      b = (chunk & 3)   << 4 // 3   = 2^2 - 1

      base64 += encodings[a] + encodings[b] + '=='
    } else if (byteRemainder == 2) {
      chunk = (bytes[mainLength] << 8) | bytes[mainLength + 1]

      a = (chunk & 64512) >> 10 // 64512 = (2^6 - 1) << 10
      b = (chunk & 1008)  >>  4 // 1008  = (2^6 - 1) << 4

      // Set the 2 least significant bits to zero
      c = (chunk & 15)    <<  2 // 15    = 2^4 - 1

      base64 += encodings[a] + encodings[b] + encodings[c] + '='
    }

    return base64
}

/** Function to perform symmetric encryption using fernet - encrypts
 *  'data' with 'key'
 */
function fernet_encrypt(key, data)
{
    var token = new fernet.Token({
        secret: new fernet.Secret(key)
    });

    encrypted = token.encode(data);

    return encrypted;
}

/** Function to perform symmetric decryption using fernet - decrypts
 *  'data' with 'key'
 */
function fernet_decrypt(key, data)
{
    var token = new fernet.Token({
        secret: new fernet.Secret(key),
        token: data,
        ttl: 0
    });

    var result = token.decode();

    return result;
}

/** Function that encrypts the passed data with the passed public key */
async function _encryptData(key, data)
{
    key = await key;

    console.log(`encrypt ${data} using ${key}`);

    // we will encrypt the message using fernet, and send that prefixed
    // by the RSA-encrypted secret. The fernet secret is a random 32 bytes
    // that are then base64 encoded
    var array = new Uint8Array(32);
    window.crypto.getRandomValues(array);
    var secret = _base64ArrayBuffer(array);

    var token = new fernet.Token({
        secret: new fernet.Secret(secret)
    });

    encrypted = token.encode(data);

    // now we will encrypt the fernet secret using the public key
    let result = await window.crypto.subtle.encrypt(
                    {
                        name: "RSA-OAEP"
                    },
                    key,
                    string_to_utf8_bytes(secret).buffer
                );

    // finally concatenate both outputs together into a single binary array
    var output = new Uint8Array(result);
    output = _concatenate(Uint8Array, output, string_to_utf8_bytes(encrypted));

    return output;
}

/** Function that decrypts the passed data with the passed private key */
async function _decryptData(key, data)
{
    // the first rsa_key_size bytes hold the rsa-encrypted fernet
    // secret to decode the rest of the message
    let secret = await window.crypto.subtle.decrypt(
                {
                    name: "RSA-OAEP",
                },
                key,
                data.slice(0,_rsa_key_size))
            ;

    secret = utf8_bytes_to_string(secret);

    if (data.length <= _rsa_key_size){
        // the secret is the message - no fernet decoding needed
        return secret;
    }

    data = utf8_bytes_to_string(data.slice(_rsa_key_size, data.length));

    var token = new fernet.Token({
        secret: new fernet.Secret(secret),
        token: data,
        ttl: 0
    });

    let result = token.decode();

    return result;
}

/** Function to generate a public/private key pair */
async function _generateKeypair()
{
    keys = await window.crypto.subtle.generateKey(
        {
            name: "RSA-OAEP",
            modulusLength: 8*_rsa_key_size,
            publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
            hash: {name: "SHA-256"}
        },
        false,
        ["encrypt", "decrypt"]
    );

    return keys;
}

/** This class provides a simple handle to a private key. This
 *  can be used to decrypt data for Acquire, and also to
 *  sign messages
 */
class PrivateKey
{
    constructor(auto_generate=true)
    {
        if (auto_generate)
        {
            this._keys = _generateKeypair();
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

    async public_key()
    {
        if (this.is_null()){ return undefined;}
        else
        {
            var keys = await this._keys;
            return new PublicKey(keys.publicKey);
        }
    }

    async decrypt(message)
    {
        if (this.is_null()){ return undefined;}
        else
        {
            var keys = await this._keys;
            return await _decryptData(keys.privateKey, message);
        }
    }
}

/** This class provides a simple handle to a public key. This
 *  can be used to encrypt data for Acquire, and also to
 *  verify signatures
 */
class PublicKey
{
    constructor(public_key=undefined)
    {
        this._key = public_key;
    }

    is_null()
    {
        return this._key == undefined;
    }

    async encrypt(message)
    {
        return await _encryptData(this._key, message);
    }

    async to_data()
    {
        if (this.is_null()){ return undefined; }

        var pem = await _exportPublicKey(this._key);
        console.log(`to_data pem = ${pem}`);
        var b = bytes_to_string(string_to_utf8_bytes(pem));
        console.log(`b = ${b}`);

        var data = {};
        data["bytes"] = b;

        return data;
    }

    static async from_data(data)
    {
        if (data == undefined){ return undefined;}

        var key = new PublicKey();

        var b = data["bytes"];

        console.log(`bytes = ${data["bytes"]}`);
        var pem = string_to_bytes(data["bytes"]);
        pem = utf8_bytes_to_string(pem);
        console.log(`pem = ${pem}`);

        key._key = await _importPublicKey(pem);

        return key;
    }
}
