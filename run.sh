#!/bin/bash

export PYTHONPATH=`pwd`
POX=./pox/pox.py

mkdir -p out
sudo ./topo.py &
$POX riplpox.riplpox --topo=dcell,1 --routing=dcell

echo Would plot now.
python plot/plot_rate.py -f out/txrate.txt -i "54h-eth1" -o plot.png --maxy=120
python plot/plot_rate.py -f out/txrate.txt -i "11h-eth(2|3)" -o plot2.png --maxy=120
