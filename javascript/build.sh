#!/bin/bash

# Just merge all of the js files into a single file,
# as javascript can't include files itself!
cat AcquireClient/*.js > acquire.js

# Now merge all of the files for the login page into ../index.html
inliner login.html > ../index.html
