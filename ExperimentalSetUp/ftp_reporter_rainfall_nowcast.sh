#!/usr/bin/env bash

# Define file names.
waterLevelFile="WaterLevel_in_mm.txt"
rainfallNowcastFile="RainfallNowcast.txt"
pathSSHKey=""

while [ true ] ; do inotifywait -e modify file.txt && scp -i $pathSSHKey $rainfallNowcastFile ubuntu@:~/ ; done