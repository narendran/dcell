#!/bin/bash

export PYTHONPATH=.
mn --custom ripl/mn.py --topo dcell,0 --controller=remote --mac
