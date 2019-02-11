#!/bin/bash

cd html && inliner password.html > ../index.html && cd -
touch index.html
