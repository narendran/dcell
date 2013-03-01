#!/bin/bash

export PYTHONPATH=`pwd`
POX=~/pox/pox.py

$POX riplpox.riplpox --topo=dcell,1 --routing=dcell
