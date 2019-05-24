
function RemoteFunctionCallError(message)
{
    console.log(`RemoteFunctionCallError(${message})`);
    const error = new Error(message);
    return error;
}

RemoteFunctionCallError.prototype = Object.create(Error.prototype);

function PermissionError(message)
{
    console.log(`PermissionError(${message})`);
    const error = new Error(message);
    return error;
}

PermissionError.prototype = Object.create(Error.prototype);

function LoginError(message)
{
    console.log(`LoginError(${message})`);
    const error = new Error(message);
    return error;
}

LoginError.prototype = Object.create(Error.prototype);

function ServiceError(message)
{
    console.log(`ServiceError(${message})`);
    const error = new Error(message);
    return error;
}

ServiceError.prototype = Object.create(Error.prototype);
