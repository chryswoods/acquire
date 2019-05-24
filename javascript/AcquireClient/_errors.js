
class RemoteFunctionCallError
{
    constructor(error)
    {
        console.log(`RemoteFunctionCallError(${error})`);
        this.message = error;
    }
}

class PermissionError
{
    constructor(error)
    {
        console.log(`PermissionError(${error})`);
        this.message = error;
    }
}

class LoginError
{
    constructor(error)
    {
        console.log(`LoginError(${error})`);
        this.message = error;
    }
}

class ServiceError
{
    constructor(error)
    {
        console.log(`ServiceError(${error})`);
        this.message = error;
    }
}
