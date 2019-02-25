import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="acquire",
    version="0.0.5",
    python_requires='>=3.6.0',
    author="Christopher Woods",
    author_email="chryswoods@gmail.com",
    description="A serverless identity, access, accounting, storage and compute management system",
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
        "requests>=2.10"
        # note that qrcode is an optional dependency
    ]
)
