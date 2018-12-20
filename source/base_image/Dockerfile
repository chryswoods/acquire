# Build and install dependencies into the build container
FROM fnproject/python:3.7-dev as build-stage

WORKDIR /function

# Install libraries needed by python dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -qy \
    build-essential \
    gcc \
    cmake \
    libgnutls28-dev \
    libcurl4-gnutls-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD requirements.txt .

RUN pip3 install --target /python/ --no-cache --no-cache-dir \
                 -r requirements.txt && \
    rm -fr ~/.cache/pip /tmp* requirements.txt func.yaml Dockerfile .venv

ENTRYPOINT ["bash"]

# Now transfer what is needed to the production container
FROM fnproject/python:3.7

# Configure environment
ENV SHELL=/bin/bash \
    FN_USER=fnuser \
    FN_UID=1000 \
    FN_GID=100

ENV HOME=/function
COPY --from=build-stage /function $HOME

ADD fix-permissions /usr/bin/fix-permissions

# Create fn user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN useradd -m -s /bin/bash -N -u $FN_UID $FN_USER && \
    fix-permissions $HOME

WORKDIR /function

COPY --from=build-stage /python /python

RUN mkdir /extralibs

# Copy libraries needed by pycurl
COPY --from=build-stage /usr/lib/x86_64-linux-gnu/libgnutls.so.30 \
                        /usr/lib/x86_64-linux-gnu/libcurl-gnutls.so.4 \
                        /usr/lib/x86_64-linux-gnu/libnghttp2.so.14 \
                        /usr/lib/x86_64-linux-gnu/libidn2.so.0 \
                        /usr/lib/x86_64-linux-gnu/librtmp.so.1 \
                        /usr/lib/x86_64-linux-gnu/libssh2.so.1 \
                        /usr/lib/x86_64-linux-gnu/libpsl.so.5 \
                        /usr/lib/x86_64-linux-gnu/libnettle.so.6 \
                        /usr/lib/x86_64-linux-gnu/libgssapi_krb5.so.2 \
                        /usr/lib/x86_64-linux-gnu/libkrb5.so.3 \
                        /usr/lib/x86_64-linux-gnu/libk5crypto.so.3 \
                        /usr/lib/x86_64-linux-gnu/liblber-2.4.so.2 \
                        /usr/lib/x86_64-linux-gnu/libldap_r-2.4.so.2 \
                        /usr/lib/x86_64-linux-gnu/libp11-kit.so.0 \
                        /usr/lib/x86_64-linux-gnu/libunistring.so.0 \
                        /lib/x86_64-linux-gnu/libidn.so.11 \
                        /usr/lib/x86_64-linux-gnu/libtasn1.so.6 \
                        /usr/lib/x86_64-linux-gnu/libnettle.so.6 \
                        /usr/lib/x86_64-linux-gnu/libhogweed.so.4 \
                        /usr/lib/x86_64-linux-gnu/libgmp.so.10 \
                        /usr/lib/x86_64-linux-gnu/libkrb5support.so.0 \
                        /lib/x86_64-linux-gnu/libkeyutils.so.1 \
                        /usr/lib/x86_64-linux-gnu/libsasl2.so.2 \
                        /extralibs/

ENV PYTHONPATH=/python \
    LD_LIBRARY_PATH=/extralibs:$LD_LIBRARY_PATH

# Copy in the updated version of oci's __init__.py that we
# have fixed to lazy load modules (thereby making it much quicker)
ADD fixed/fast_oci__init__.py /python/oci/__init__.py
ADD fixed/fast_oci_object_storage__init__.py /python/oci/object_storage/__init__.py
#ADD fixed/fast_oci_object_storage_models__init__.py /python/oci/object_storage/models/__init__.py
#ADD fixed/fast_oci__vendor__init__.py /python/oci/_vendor/__init__.py

ADD fixed/fast_fdk__init__.py /python/fdk/__init__.py

# Add the function last as this is the thing that will change
# most often
ENV PYTHON_EXT=/function/python_modules

RUN mkdir $PYTHON_EXT
ADD Acquire $PYTHON_EXT/Acquire

ENV PYTHONPATH=$PYTHONPATH:$PYTHON_EXT

RUN python3 -m compileall $PYTHON_EXT/Acquire/*

ENTRYPOINT ["bash"]

# Become the $FN_USER so that nothing runs as root
USER $FN_USER
