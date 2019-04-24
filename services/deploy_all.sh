#!/bin/bash

cd base_image && ./build_and_push.sh && cd -
cd identity && fn --verbose deploy --local --all && cd -
cd access && fn --verbose deploy --local --all && cd -
cd accounting && fn --verbose deploy --local --all && cd -
cd storage && fn --verbose deploy --local --all && cd -
cd registry && fn --verbose deploy --local --all & cd -
