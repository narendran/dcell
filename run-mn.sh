#!/bin/bash

export PYTHONPATH=.
mn --custom ripl/mn.py --topo dcell,1 --controller=remote --mac
