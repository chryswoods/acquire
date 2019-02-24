import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="acquire",
    version="0.0.1",
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
)
