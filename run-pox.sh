#!/bin/bash

export PYTHONPATH=`pwd`
POX=~/pox/pox.py

$POX riplpox.riplpox --topo=dcell,0 --routing=dcell
