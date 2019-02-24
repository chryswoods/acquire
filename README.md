# Acquire

[![Build Status](https://dev.azure.com/bristolrse/Acquire/_apis/build/status/chryswoods.acquire?branchName=master)](https://dev.azure.com/bristolrse/Acquire/_build/latest?definitionId=1&branchName=master)

(C) Christopher Woods 2018 - Released under the [Apache 2 License](LICENSE)

## Installation

```
pip install acquire
```

## An Access, Accounting and Authorisation (Identity) Infrastructure for the Cloud

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

## Cloud Native and Highly Scalable

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
when Acquire functions are called. As demand increases, more resources
are provisioned to automatically scale with the load.

## Distributed

The three services in Acquire build on top of each other, yet are
completely separated. Each service is designed to run on its own
object store / Fn server, thereby allowing them to be distributed
between multiple services in multiple regions (and even between
multiple cloud providers). Separation of services increases security,
as compromising the accounting service would not have any impact
on the identity service (not that compromising any service should
be easy!).

## Secure

Acquire builds on top of standard cryptography libraries and uses
the production APIs of the underlying cloud provider where possible.
The security mechanism of the underlying object store is fully
utilised (all movement of object data is encrypted, and data is
encrypted at rest with rotating keys). In addition, input
and output data from the underlying serverless functions is
encrypted and signed using industry standard libraries and
algorithms (SSL, [Python cryptography](https://cryptography.io/en/latest/)
and [Javascript Web Cryptography API](https://www.w3.org/TR/WebCryptoAPI/)).
In detail, 2048-bit RSA keys with SHA256 hashing and MGF1 padding
are used to encrypt and share [Fernet](https://medium.com/coinmonks/if-youre-struggling-picking-a-crypto-suite-fernet-may-be-the-answer-95196c0fec4b)
generated secrets with symmetric Fernet encryption. Fernet
generates URL safe encoded keys, uses 128-bit AES in CBC mode
and PKCS7 padding, with HMAC using SHA256. Signing and verification
uses 2048-bit RSA keys with MGF1 padding using a SHA256 hash
and a random salt.

To simplify use of cryptography in the Python parts of Acquire, it is fully wrapped
into a simple [Acquire.Crypto](source/Acquire/Crypto) library,
with all encryption, decryption, signing and verification handled
via [Acquire.Crypto.Keys](source/Acquire/Crypto/_keys.py)
(with corresponding Javascript code in [acquire_crypto.js](source/identity/s/html/acquire_crypto.js)).
In addition, users authenticate both with passwords and with
one-time-codes that are generated using the [PyOTP](https://github.com/pyauth/pyotp)
library, which follows [RFC 6238](https://tools.ietf.org/html/rfc6238)
to produce google-authenticator-compatible time-based one-time
password codes. These are rigorously checked by Acquire, with
record keeping used to ensure that each code is used only once.

