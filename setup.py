import setuptools


def get_version():
    """get_version - thanks to
       https://milkr.io/kfei/5-common-patterns-to-version-your-Python-package
    """
    import os
    import re
    VERSIONFILE = os.path.join('Acquire', '__init__.py')
    initfile_lines = open(VERSIONFILE, 'rt').readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError('Unable to find version string in %s.' % (VERSIONFILE,))


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="acquire",
    version=get_version(),
    python_requires='>=3.6.0',
    author="Christopher Woods",
    author_email="chryswoods@gmail.com",
    description="A serverless identity, access, accounting, storage and "
                "compute management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chryswoods/acquire",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License  ",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
           "acquire_login = Acquire.Client.Scripts.__acquire_login__:main"
        ]
    },
    install_requires=[
        "pyotp>=2",
        "cachetools>=3",
        "tblib>=1.2",
        "cryptography>=2",
        "pyyaml>=3.0",
        "requests>=2.10",
        "qrcode[pil]>=5.0"
    ]
)
