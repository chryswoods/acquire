
/** Standardise the passed datetime into UTC */
function datetime_to_datetime(d)
{
    var date = new Date(d);
    var now_utc =  Date.UTC(date.getUTCFullYear(), date.getUTCMonth(),
                            date.getUTCDate(), date.getUTCHours(),
                            date.getUTCMinutes(), date.getUTCSeconds());

    return new Date(now_utc);
}

/** Convert the passed datetime into a standard formatted string */
function datetime_to_string(d)
{
    d = datetime_to_datetime(d);
    return d.toISOString();
}

/** Convert the passed string back into a datetime */
function string_to_datetime(s)
{
    return datetime_to_datetime(Date.parse(s));
}

/** Convert the passed string back to bytes */
function string_to_bytes(s)
{
    s = unescape(encodeURIComponent(s));
    return atob(s);
}

/** Convert the passed string to a utf-8 string */
function string_to_utf8_bytes(s)
{
    return new TextEncoder("utf-8").encode(s);
}

/** Convert the passed bytes to a safe string */
function bytes_to_string(b)
{
    return btoa(b);
}
