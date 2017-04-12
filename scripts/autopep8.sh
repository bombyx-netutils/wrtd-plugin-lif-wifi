#!/bin/bash

LIBFILES="$(find ./lif_wifi -name '*.py' | tr '\n' ' ')"

autopep8 -ia --ignore=E501 ${LIBFILES}
