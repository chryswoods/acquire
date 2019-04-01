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
10. Please always add tests for your new code. We use `pytest` for testing. Please place 
    individual tests of your class into the appropriate `test/pytest` directory, and tests that
    require mocking of the service into the appropriate `test/pytest/mock` directory.
11. Please don't add new dependencies to Acquire without first consulting the full range of functionality
    available in the standard python library and the existing dependencies. If you add a new 
    dependency then please make this clear in your pull request, together with a justification of why
    this is needed. We need to minimise the dependencies of Acquire to ensure it can be installed
    easily on the widest range of devices.
12. Development takes place in the `devel` branch. Only once this has been reviewed will we issue
    a pull request into the `master` branch. All merges into `master` will trigger a rebuild and 
    resubmission of Acquire to pip (therefore each `pip install acquire` release will correspond to
    a version of Acquire in `master`)
13. Do not commit code directly to `master` or `devel`. Please work in a feature branch, and then issue
    a pull request into `devel` once your feature is ready. Ensure that there are sufficient tests 
    included with your feature to enable a proper code review to complete. Please be willing to 
    answer questions on your pull request. Also please ensure that you have merged all recent
    changes from `devel` into your feature branch so that your feature can be merged automatically
    if it is accepted.
