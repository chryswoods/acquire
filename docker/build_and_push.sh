#!/bin/bash

rsync -a --verbose ../../Acquire . --exclude '__pycache__' --exclude '.git'
rsync -a --verbose ../admin . --exclude '__pycache__'

docker build -t garj/acquire-base:latest .

rm -rf Acquire admin

# docker push garj/acquire-base:latest

#docker run --rm -it chryswoods/acquire-base:latest
