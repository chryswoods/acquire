FROM chryswoods/acquire-base:latest

# Need to be user root or Fn exits with
# {"message":"internal server error"}
USER root

ADD serve.py $HOME/
RUN python3 -m compileall $HOME/*.py

ADD index.html $HOME/

ENTRYPOINT ["python", "serve.py"]
