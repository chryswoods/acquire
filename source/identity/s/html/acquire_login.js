/**
 *  Javascript needed to implement equivalent of acquire_login command
 *  line tool in a browser
 *
 */

/** Hard code the URL of the identity service */
var identity_service_url = "http://130.61.60.88:8080/t/identity"

/** Also hard code the data for the service's public key
 *
 *  This data is encoded using the PublicKey.to_data() function...
*/
var identity_public_pem = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFzR0cycjJXWXljR0t0MXEzc1hZdAprbkZaVjVSa1Z5TUV2M2VZS2o0VDExMG41b241bzBBNms1NU13cTZPVFZpUVhLVVd3enQ0K09oWDY4cXNjM2ZPCnZ2aFFZdGZpT2prcXJvNFI0djhXaXdxbjlwdmdocW04b1FmTlhqRWw1ODBvV0w4SFMzTFgvQk9TQVFyMHNpQkYKN0hMWW9QVlVrcVovdmFuUWlwWlJhNXZmTlZoNXVBcGs0b2xRRzJzL3kyZnVSZzQydEhpbldObk1YdE0wWTVGbgprV1lUK00xL3BrUDRpSVB0akg0VUg0OTQyaG5SSkRwZXArWWpJQ1g5eVZQcHRSbFhIdWYrbVVtTThNZGpHcFp1Cks3cHppTGh6L2tNNzcwejhlMEluYzEzcFNBV2VLRmRKbjFMa3F2a24vVU9XN1pMVVV6Q1VKdGZ2VjlJb0hkbVcKZ1FJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==";

/** Hard code the key size (in bytes) as javascript web crypto doesn't
 *  seem to have a way to query this programatically. 256 bytes (2048 bit)
 *  is used on the server in all of the python functions
*/
var rsa_key_size = 256;

/** Get URL requestion variables as an array. This is inspired from
 *  https://html-online.com/articles/get-url-parameters-javascript/
 */
function getUrlVars(url) {
    if (!url){
        url = window.location.href
    }

    var vars = {};
    var parts = url.replace(/[?&]+([^=&]+)=([^&]*)/gi,
                                             function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

/** Write local data to the browser with 'name' == 'value' */
function writeData(name, value)
{
    if (typeof(Storage) != "undefined") {
        localStorage.setItem(name, value);
        console.log(`SAVED ${name} == ${value}`);
    } else {
        console.log("Sorry - no web storage support. Cannot cache details!");
    }
}

/** Remove local data at key 'name' */
function clearData(name)
{
    if (typeof(Storage) !== "undefined") {
        return localStorage.removeItem(name);
    } else {
        console.log("Sorry - no web storage support. Cannot cache details!");
        return null;
    }
}

/** Read local data from the browser at key 'name'. Returns
 *  NULL if no such data exists
 */
function readData(name)
{
    if (typeof(Storage) !== "undefined") {
        return localStorage.getItem(name);
    } else {
        console.log("Sorry - no web storage support. Cannot cache details!");
        return null;
    }
}

/** Get the session UID from the URL request parameters. The
 *  URL will have the form http[s]://example.com:8080/t/identity/u?id=XXXXXX
 */
function getSessionUID() {
  vars = getUrlVars();

  return session_uid = vars["id"];
}

/** Function to return whether or not we are running in testing
 *  mode - this is signified by a URL request parameter "testing"
 *  being equal to anything that is not false
 */
function isTesting(){
  vars = getUrlVars();
  return vars["testing"];
}

/** Function to return the fully qualified URL of the identity service */
function getIdentityServiceURL(){
  return identity_service_url;
}

/** Convert a string to utf-8 encoded binary bytes */
function to_utf8(s){
    var encoded = new TextEncoder("utf-8").encode(s);
    return encoded;
}

/** Synonym for to_utf8 */
function string_to_utf8_bytes(s){
    return to_utf8(s);
}

/** Decode utf-8 encoded bytes to a string */
function from_utf8(b){
    var decoded = new TextDecoder("utf-8").decode(b);
    return decoded;
}

/** Synonym for from_utf8  */
function utf8_bytes_to_string(b){
    return from_utf8(b);
}

/** Function to convert from a string back to binary */
function string_to_bytes(s){
    return base64js.toByteArray(s);
}

/** Function to convert binary data to a string */
function bytes_to_string(b){
    return base64js.fromByteArray(b);
}

/** Function used as part of converting a key to a pem file */
function arrayBufferToBase64String(arrayBuffer) {
    var byteArray = new Uint8Array(arrayBuffer)
    var byteString = ''
    for (var i=0; i<byteArray.byteLength; i++) {
        byteString += String.fromCharCode(byteArray[i])
    }
    return btoa(byteString)
}

/** Function to convert a base64 string to an array buffer */
function base64StringToArrayBuffer(b64str) {
    var byteStr = atob(b64str)
    var bytes = new Uint8Array(byteStr.length)
    for (var i = 0; i < byteStr.length; i++) {
        bytes[i] = byteStr.charCodeAt(i)
    }
    return bytes.buffer
}

/** Function used to convert binary key date to pem */
function convertBinaryToPem(binaryData, label) {
    var base64Cert = arrayBufferToBase64String(binaryData)
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

/** Function that converts the passed public key into an Acquire
 *  json dictionary
 */
async function exportPublicKeyToAcquire(key){
    var pem = await exportPublicKey(key);
    return bytes_to_string(to_utf8(pem));
}

/** Function to convert a public key to a PEM file */
async function exportPublicKey(key) {
    let exported = await window.crypto.subtle.exportKey('spki', key);
    let pem = convertBinaryToPem(exported, "PUBLIC KEY");
    return pem;
}

/** Function to import a public key from the passed json data */
function getIdentityPublicPem(){
    return utf8_bytes_to_string(base64js.toByteArray(identity_public_pem));
}

/** Function to generate a public/private key pair */
async function generateKeypair(){
    keys = await window.crypto.subtle.generateKey(
        {
            name: "RSA-OAEP",
            modulusLength: 8*rsa_key_size,
            publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
            hash: {name: "SHA-256"}
        },
        false,
        ["encrypt", "decrypt"]
    );

    return keys;
}

/** Generate a fernet key from the supplied username and password - this will always
 *  return the same key for the same username and password combination
 */
async function generateFernetKey(username, password){
    // using a constant salt as we want the same key to be generated from
    // the same password! (these were randomly generated...)
    var salt = new Uint8Array([241, 21, 50, 59, 169, 41, 4, 123, 44, 41, 82,
                               92, 72, 43, 252, 109]);

    const params = {name: "PBKDF2", hash: {name: "SHA-1"}, iterations: 1000,
                    salt: salt};

    const encoder = new TextEncoder("utf-8");
    const buffer = encoder.encode(username + password);
    const key = await crypto.subtle.importKey("raw", buffer, "PBKDF2", false, ["deriveBits"]);
    const derivation = await crypto.subtle.deriveBits(params, key, 256);

    return base64ArrayBuffer(derivation);
}

/** Function to convert pemfile info binary data used for js crypto */
function convertPemToBinary(pem) {
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
    return base64StringToArrayBuffer(encoded)
}

/** Function to import and return the public key from the passed pemfile */
 async function importPublicKey(pemKey) {
    //convert the pem key to binary
    var bin = convertPemToBinary(pemKey);

    var encryptAlgorithm = {
        name: "RSA-OAEP",
        modulusLength: 8*rsa_key_size,
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

/** Function to load the public key of the identity service */
async function getIdentityPublicKey(){
    var pem = getIdentityPublicPem();
    return await importPublicKey(pem);
}

/** Function that concatenates two arrays together -
 *  thanks to http://2ality.com/2015/10/concatenating-typed-arrays.html
 */
function concatenate(resultConstructor, ...arrays) {
    let totalLength = 0;
    for (let arr of arrays) {
        totalLength += arr.length;
    }
    let result = new resultConstructor(totalLength);
    let offset = 0;
    for (let arr of arrays) {
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
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
function base64ArrayBuffer(arrayBuffer) {
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
function fernet_encrypt(key, data){
    var token = new fernet.Token({
        secret: new fernet.Secret(key)
    });

    encrypted = token.encode(data);

    return encrypted;
}

/** Function to perform symmetric decryption using fernet - decrypts
 *  'data' with 'key'
 */
function fernet_decrypt(key, data){
    var token = new fernet.Token({
        secret: new fernet.Secret(key),
        token: data,
        ttl: 0
    });

    var result = token.decode();

    return result;
}

/** Function that encrypts the passed data with the passed public key */
async function encryptData(key, data){
    key = await key;

    // we will encrypt the message using fernet, and send that prefixed
    // by the RSA-encrypted secret. The fernet secret is a random 32 bytes
    // that are then base64 encoded
    var array = new Uint8Array(32);
    window.crypto.getRandomValues(array);
    var secret = base64ArrayBuffer(array);

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
    output = concatenate(Uint8Array, output, string_to_utf8_bytes(encrypted));

    return output;
}

/** Function that decrypts the passed data with the passed private key */
async function decryptData(key, data){
    // the first rsa_key_size bytes hold the rsa-encrypted fernet
    // secret to decode the rest of the message
    let secret = await window.crypto.subtle.decrypt(
                {
                    name: "RSA-OAEP",
                },
                key,
                data.slice(0,rsa_key_size))
            ;

    secret = utf8_bytes_to_string(secret);

    if (data.length <= rsa_key_size){
        // the secret is the message - no fernet decoding needed
        return secret;
    }

    data = utf8_bytes_to_string(data.slice(rsa_key_size, data.length));

    var token = new fernet.Token({
        secret: new fernet.Secret(secret),
        token: data,
        ttl: 0
    });

    let result = token.decode();

    return result;
}

/** Below function inspired by TOTP generator at
 * https://www.thepolyglotdeveloper.com/2014/10/generate-time-based-one-time-passwords-javascript/
 *
 * Adapted to use webcrypto hmac function
 */
TOTP = function() {

    var dec2hex = function(s) {
        return (s < 15.5 ? "0" : "") + Math.round(s).toString(16);
    };

    var hex2dec = function(s) {
        return parseInt(s, 16);
    };

    var leftpad = function(s, l, p) {
        if(l + 1 >= s.length) {
            s = Array(l + 1 - s.length).join(p) + s;
        }
        return s;
    };

    var base32tohex = function(base32) {
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
            var epoch = Math.round(new Date().getTime() / 1000.0);
            var time = leftpad(dec2hex(Math.floor(epoch / 30)), 16, "0");
            var hmacObj = new jsSHA(time, "HEX");
            var hmac = hmacObj.getHMAC(base32tohex(secret), "HEX", "SHA-1", "HEX");
            var offset = hex2dec(hmac.substring(hmac.length - 1));
            var otp = (hex2dec(hmac.substr(offset * 2, 8)) & hex2dec("7fffffff")) + "";
            otp = (otp).substr(otp.length - 6, 6);
        } catch (error) {
            throw error;
        }
        return otp;
    };

}

/** Below functions are all for the form-to-json code.
 *
 *  Form to JSON code is inspired heavily from excellent tutorial here
 *  https://code.lengstorf.com/get-form-values-as-json/
 */

/**
  * Checks that an element has a non-empty `name` and `value` property.
  * @param  {Element} element  the element to check
  * @return {Bool}             true if the element is an input, false if not
*/
var isValidElement = function isValidElement(element) {
    return element.name && element.value;
};

/**
  * Checks if an element’s value can be saved (e.g. not an unselected checkbox).
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the value should be added, false if not
*/
var isValidValue = function isValidValue(element) {
    return !['checkbox', 'radio'].includes(element.type) || element.checked;
};

/**
  * Checks if an input is a checkbox, because checkboxes allow multiple values.
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the element is a checkbox, false if not
*/
var isCheckbox = function isCheckbox(element) {
    return element.type === 'checkbox';
};

/**
  * Checks if an input is a `select` with the `multiple` attribute.
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the element is a multiselect, false if not
*/
var isMultiSelect = function isMultiSelect(element) {
    return element.options && element.multiple;
};

/**
  * Retrieves the selected options from a multi-select as an array.
  * @param  {HTMLOptionsCollection} options  the options for the select
  * @return {Array}                          an array of selected option values
*/
var getSelectValues = function getSelectValues(options) {
    return [].reduce.call(options, function (values, option) {
        return option.selected ? values.concat(option.value) : values;
    }, []);
};

/**
  * Retrieves input data from a form and returns it as a JSON object.
  * @param  {HTMLFormControlsCollection} elements  the form elements
  * @return {Object}                               form data as an object literal
  */
var formToJSON = function formToJSON(elements)
{
    return [].reduce.call(elements, function (data, element) {
        // Make sure the element has the required properties and
        // should be added.
        if (isValidElement(element) && isValidValue(element)) {
            /*
             * Some fields allow for more than one value, so we need to check if this
             * is one of those fields and, if so, store the values as an array.
             */
            if (isCheckbox(element)) {
                var values = (data[element.name] || []).concat(element.value);
                if (values.length == 1){
                values = values[0];
                }
                data[element.name] = values;
            } else if (isMultiSelect(element)) {
                data[element.name] = getSelectValues(element);
            } else {
                data[element.name] = element.value;
            }
        }

        return data;
    },
    {});
};

