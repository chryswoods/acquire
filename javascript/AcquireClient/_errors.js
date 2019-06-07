
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
