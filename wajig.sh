#!/bin/sh

if [ -z "$1" ]; then
    /usr/share/wajig/shell.py
else
    /usr/bin/python3 /usr/share/wajig/wajig.py "$@"
fi
