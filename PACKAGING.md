# Instructions for packaging Acquire

The Acquire Python module comprises two parts:

1. The Acquire module itself, in directory `Acquire`. This provides
   all common code plus the `Acquire.Client` library used by the
   user-facing clients.
2. The services themselves, in directory `services`

Only the `Acquire` module itself is packaged and installed via pip.

To do this, ensure you have the latest versions of setuptools and wheel installed;

```
python3 -m pip install --user --upgrade setuptools wheel
```

Now run this command from the same directory where setup.py is located

```
python3 setup.py sdist bdist_wheel
```

Now ensure you have the latest version of twine installed

```
python3 -m pip install --user --upgrade twine
```

Next upload to pypi, using

```
python3 -m twine upload dist/*
```

