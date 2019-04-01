Contributions to Acquire are very welcome :-)

We have a few rules that help ensure acquire will work across all supported platforms and
that the code maintains a coherent look and feel. Please try to follow the below rules,
and get in touch with us (raise and issue or issue a pull request) if you have any questions
or want to make any changes.

1. Code is written in pure Python >= 3.6
2. All imported modules should (as far as possible) be pure Python, ideally installable via pip
3. Classes are named in `CamelCase` (first letter capitalised). Functions are `lower_case` with
   underscore separating words. All variables must be private, written in `_lower_case` with
   starting underscore. Member variables of a class must only be changed by member functions
   of that class. Avoid global variables wherever possible.
4. Where possible, please pass arguments to functions by name. This will help maintain backwards
   compatibility as we evolve the API over time, e.g.

```python
def my_function(arg1, arg2):
    do_something

result = my_function(arg1=42, arg2="hello")
```

5. All code should score highly via the pylint and pep8 tools (ideally 100%). We recommend developing
   using an IDE that highlights pep8 compliance, e.g. vscode or pycharm
6. Please type-check arguments where needed (use `isinstance(arg, ArgClass)` to validate arguments
   are of the correct type).
   This is particularly important for data received from
   the user, as security holes may be opened if the user is able to pass their own classes to
   the serverless functions.
7. Because Acquire is used in a serverless framework, we must keep import times small (ideally
   milliseconds). Because of this, you must avoid importing modules at the top of files. Instead,
   you should import parts of modules only as you need them, and ensure that you import them
   into a hidden name or namespace (starting with an underscore) e.g.

```python
def my_function():
    from somemodule import something as _something
    _something.run()
```

8. Please add `to_data(self)` and static `from_data(data)` functions to all classes so that they
   can be serialised and deserialised from json-derived data. The `to_data` function must return
   an object (normally dictionary) that can be serialised to json via the `json.dumps` function, while
   the `from_data` function must rebuild your object from data returned from a `json.loads` function.
9. Please use the functions provided in `Acquire.ObjectStore._encoding.py` to convert data and
   construct data. Functions here include generating the current UTC datetime, converting between
   strings and lots of other data types etc. Using these functions will ensure that (1) all datetimes
   are constructed as UTC and are consistent, and that (2) all data is encoded and decoded in a
   consistent way.
10. Please add sufficient documentation for your new code. All functions
    and classes should include source-level documentation. Ideally you
    should also provide examples of how to use your code, both as
    documentation, possibly also a Jupyter notebook (in the appropriate
    `notebooks` directory) and also as tests that demonstrate usage.
11. Please always add tests for your new code. We use `pytest` for testing. Please place
    individual tests of your class into the appropriate `test/pytest` directory, and tests that
    require mocking of the service into the appropriate `test/pytest/mock` directory.
12. Please don't add new dependencies to Acquire without first consulting the full range of functionality
    available in the standard python library and the existing dependencies. If you add a new
    dependency then please make this clear in your pull request, together with a justification of why
    this is needed. We need to minimise the dependencies of Acquire to ensure it can be installed
    easily on the widest range of devices.
13. Development takes place in the `devel` branch. Only once this has been reviewed will we issue
    a pull request into the `master` branch. All merges into `master` will trigger a rebuild and
    resubmission of Acquire to pip (therefore each `pip install acquire` release will correspond to
    a version of Acquire in `master`)
14. Do not commit code directly to `master` or `devel`. Please work in a feature branch, and then issue
    a pull request into `devel` once your feature is ready. Ensure that there are sufficient tests
    included with your feature to enable a proper code review to complete. Please be willing to
    answer questions on your pull request. Also please ensure that you have merged all recent
    changes from `devel` into your feature branch so that your feature can be merged automatically
    if it is accepted.
15. Acquire is a client-server package. As much as possible, all
    client-facing code should be placed into the `Acquire.Client`
    module. Code needed for the services should be in the appropriate
    `Acquire.ServiceName` module, e.g. `Acquire.Identity` or
    `Acquire.Storage` etc. Code which is generic should be placed in
    base libraries, e.g. all crypto code in `Acquire.Crypto`, all
    object store and encoding/decoding code into `Acquire.ObjectStore`.
    The actual functions run on the serverless infrastructure should
    contain minimal code and be in the appropriate `services` directory,
    e.g. `services/identity`.
16. Serverless functions should be written as follows;

```python
def run(args):
    from Acquire.Service import create_return_value

    input1 = MyClass1.from_data(args["input1"])
    input2 = MyClass2.from_data(args["input2"])  # etc. etc.

    # do something

    result = create_return_value()

    result["output1"] = output1.to_data()
    result["output2"] = output2.to_data()

    return result
```

  Please just raise an exception if there is an error. This will
  be handled correctly and returned to the user.

  Once you have written your `run` function, you will need
  to add it to the `route` function of the service, e.g.
  to `services/identity/route.py`

```python
def identity_functions(function, args):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer"""
    # place your function in in alphabetical order
    elif function == "my_function":
        from identity.my_function import run as _my_function
        return _my_function(args)
    # place your function in in alphabetical order
```

17. Do not use cloud APIs directly. All cloud APIs should be hidden
    behind a common, abstracting API. For example, all use of
    object store is hidden behind the `Acquire.ObjectStore` thin-wrapper
    API.
18. Do not use functions from GPL or LGPL modules directly. Acquire
    is licensed under the Apache license and must be able to function
    without calling any GPL or LGPL code. To include a GPL module please
    add it to the `Acquire.Stubs` module and create the classes or
    call the functions indirectly. Please ensure that you detect whether
    or not the module is loaded, and if not, provide alternative
    functionality. Ideally, avoid GPL or LGPL dependencies.