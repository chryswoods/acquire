/**
 *  Javascript needed to implement equivalent of acquire_login command
 *  line tool in a browser
 *
 */

/** Hard code the URL of the identity service */
var identity_service_url = "http://fn.acquire-aaai.com:8080/t/identity"

/** Also hard code the data for the service's public key
 *
 *  This data is encoded using the PublicKey.to_data() function...
*/
var identity_public_pem = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF3WEM3YVhtclFGR2NhdVIza3FkYQphQkNhaEdYL25SdUdOZXgrUjBBNXpaMTd5MFlibFhjOFl3RnlETXg0QWtIT3lwRXMrQmlURW5pbSt3aTZpTFljCkZoaFZ3OFNiZFRSRGlSNHAvZ3lRNVV3MVdDSks3czFMUnhQQlZ4QkZBOEJPYVZ4NlFwVG85dkV0SGZKRHN0cjQKVXcvQ0hWQm1uZ3d1ZWczWWhUOU5hT1FxRGFvLzZLb0RjQnExdmlQVjBhbDE4RzZEZFU5S3JySnQrSlEwRm5DWgpnYTZlalNzbENPNW9tVHU3TllmK2dveW5GUGY3SmlSZ3VEMmRwcmVoQ2RMTWliWnNIWkZzMmhWT1lIYU1tNUN1Clk2SHpVQnBzbnFzMzN1QnRCYVhIUGZVeEhEczRwS0lnR1R3OUl6VlJOUk42WlA0NkNDMitLQWoxVGE5ZTU0Y1YKQ3dJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==";

/** Also hard code the fingerprint for the service's public key */
var identity_fingerprint = "70:3d:6d:f9:39:e5:17:6d:c9:01:cf:67:0b:d4:97:cf";

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
    if (typeof(Storage) != "undefined")
    {
        localStorage.setItem(name, value);
    }
}

/** Remove local data at key 'name' */
function clearData(name)
{
    if (typeof(Storage) !== "undefined")
    {
        return localStorage.removeItem(name);
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

/** Function to import and return the public key of the identity service
 *  to which we will connect
 */
function getIdentityPublicPem(){
    return utf8_bytes_to_string(base64js.toByteArray(identity_public_pem));
}

/** Function to return the fingerprint of the public key of the identity
 *  service to which we will connect
 */
function getIdentityFingerprint(){
    return identity_fingerprint;
}

/** Function to load the public key of the identity service */
async function getIdentityPublicKey(){
    var pem = getIdentityPublicPem();
    return await importPublicKey(pem);
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

