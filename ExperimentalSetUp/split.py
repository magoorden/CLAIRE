#!/bin/python3

import sys
import re

if len(sys.argv) != 3:
    print("Incorrect number of arguments")
    exit()


fields = sys.argv[2:]
legend = []
data = {}
with open(sys.argv[1]) as raw:
    first_line = raw.readline()
    n_simulations = int(first_line[first_line.find("(")+1:first_line.find(")")])
    
    new_file = None
    for line in raw:
        if line[0] == "#":
            second_hash = line.find("#",1)
            variable = line[2:second_hash - 1]
            variable = variable.replace("/", "")
            number = int(line[second_hash + 1:])
            if number > n_simulations:
                print(f"Found data series for simulation {number}, but only {n_simulations} simulations should exist")
                exit()
            if new_file is not None:
                new_file.close()
            new_file = open(sys.argv[1][:sys.argv[1].rindex(".")] + f"_{variable}_{number}.{sys.argv[2]}", "w")
        else:
            new_file.write(line)

    new_file.close()
