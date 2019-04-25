This directory contains all of the functions that are used by the registry
(root key serving) part of the Acquire Identity/Access/Accounting service

While the other services are designed to be user-runnable, the registry
service provides a backbone of services that are used to register and retain
public keys of other services.

There can be only a maximum of 35 registry services in the world, as each
one is given a unique letter from [a-z1-9] (number 0 is reserved for testing
registries).

The UID for a registry service is its registry letter repeated 8 times, e.g.
aaaaaaaa. The UID for any service registered by this registry is the
registry letter followed by 7 random values from [a-z1-9], e.g.
afj36cos. This supports registering 36**7 services per registry, 
which is nearly 80billion per registry. Across all registries, about
2.7trillion services could be registered, which should be enough!

