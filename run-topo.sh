#!/bin/bash

mkdir out
sudo ./topo.py
python plot/plot_rate.py -f out/txrate.txt -i "54h-eth1" -o plot.png --maxy=120
