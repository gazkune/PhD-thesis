#!/bin/bash

find -type f|grep '[1-6].*/figures/EPS/.*.eps'|xargs rm -f
