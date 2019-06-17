
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
