

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

/** This class provides a simple handle to a public key. This
 *  can be used to encrypt data for Acquire, and also to
 *  verify signatures
 */
class PublicKey
{
    constructor()
    {
        this._key = undefined;
    }

    is_null()
    {
        return this._key == undefined;
    }

    async to_data()
    {
        var data = {};

        if (this.is_null()){ return data; }

        var pem = await _exportPublicKey(this._key);
        var b = bytes_to_string(pem);

        data["bytes"] = b;

        return data;
    }

    static async from_data(data)
    {
        if (data == undefined){ return undefined;}

        var key = new PublicKey();

        var b = data["bytes"];

        var pem = string_to_bytes(data["bytes"]);

        key._key = await _importPublicKey(pem);

        return key;
    }
}
