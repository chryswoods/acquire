
class RemoteFunctionCallError extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "RemoteFunctionCallError";
        this.details = message;
        this.cause = cause;
    }
}

class PermissionError extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "PermissionError";
        this.details = message;
        this.cause = cause;
    }
}

class LoginError extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "LoginError";
        this.details = message;
        this.cause = cause;
    }
}

class ServiceError extends Error
{
    constructor(message, cause=undefined)
    {
        super(message);
        this.name = "ServiceError";
        this.details = message;
        this.cause = cause;
    }
}
