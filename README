# Acquire

## An Access, Accounting and Authorisation (Identity) Infrastructure for the Cloud

Acquire is a AAAI infrastructure for the cloud. It provides a cloud-neutral
platform to cover the following three functions:

1. Authorisation (Identity) management : Enables users to securely identify themselves
and generate secure identity tokens that can be given to other services to authorise
actions.

2. Access management : Enables users to request access to resources. Users
identify themselves via the Identity service and pass authorisation tokens to the 
access service to request access.

3. Accounting : Enables users to control and track their usage. Users identify
themselves to the identity service, request access to resources via the access
service, which then checks the accounting service to see if sufficient funds
exist to pay for access, and submits an invoice for payment. Once the access
has been provided it is receipted and funds transferred. In this way, users
have control over their spending, with a full audit trail providing 
financial and usage accounting for their use of a system. 

## Cloud Native and Highly Scalable

Acquire is built as a cloud-native application. It is written as a set of 
serverless functions which manages state via a central object store.

* Serverless: Acquire uses the open source [Fn project](http://fnproject.io).
This is a container-native serverless platform that can run anywhere -- any 
cloud or on-premise. It works by packaging up function code into docker 
containers that are executed on demand based on triggers from http/https
end-points.

* Object store: Acquire uses a thin abstraction around common object
stores to read and write all data. This provides global access to data
with high security (all object store data is encrypted in transport,
and encrypted at rest with rotating keys).

The combination of these two technologies allows Acquire to be highly
scalable. There are no "idle servers", as compute is consumed only
when Acquire functions are called. As demand increases, more resource
are provisioned to automatically scale with the load.

