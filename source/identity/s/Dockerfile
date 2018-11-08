# Build and install dependencies into the build container
FROM node:latest as build-stage

RUN apt-get update
RUN apt-get install -y ssh

# Install inliner
RUN npm install -g inliner

WORKDIR html

# Now add the files to be inlined
ADD html/* ./
ADD inline_file.sh ./

# Inline the files to create a single 'index.html'
RUN ./inline_file.sh

RUN cat index.html

# Now transfer what is needed to the production container
FROM chryswoods/acquire-base:latest

# Need to be user root or Fn exits with
# {"message":"internal server error"}
USER root

COPY --from=build-stage /html/index.html index.html

ADD *.py $HOME/
RUN python3 -m compileall $HOME/*.py

ADD index.html $HOME/

ENTRYPOINT ["python", "serve.py"]
