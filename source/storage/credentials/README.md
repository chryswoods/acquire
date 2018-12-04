This directory contains credentials. Obviously these should be local
to a machine and not uploaded to GitHub... ;-)

Generate new keys using;

$ openssl genrsa -des3 -out storage-service.pem 2048
$ openssl rsa -in storage-service.pem -outform PEM -pubout -out storage-service_public.pem
