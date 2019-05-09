#!/bin/bash

# Just merge all of the js files into a single file,
# as javascript can't include files itself!
cat AcquireClient/*.js > acquire.js
