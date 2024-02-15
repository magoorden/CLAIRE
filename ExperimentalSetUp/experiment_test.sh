#!/usr/bin/env bash

# Define file names.
waterLevelFileFtp="/var/sftp/Waterlevel/WaterLevel_in_mm.txt"
RainfallNowcastFileFtp="/var/sftp/RainfallNowcast/RainfallNowcast.txt"
waterLevelFileLocal="WaterLevel_in_mm.txt"
RainfallNowcastFileLocal="RainfallNowcast.txt"
controlFile="/var/sftp/Control/control_state.txt"

modelTemplate="pond_online_template.xml"
model="pond_online.xml"
query="query.q"
verifyta="verifyta5"

result="result.log"
state="state.log"
control="control-action.log"

# Period in time units (minutes). 
# Make sure this corresponds to the model (is not checked in this script).
period=10
# How many periods to compute strategy for.
horizon=12
# Duration of experiment in time unites (minutes).
duration=120

# The time of the last Uppaal calculation
timeLast=0
# The number of steps performed.
step=0

# Insert rainfall nowcast path in model.
folder=$(pwd)
path="$folder"/"$RainfallNowcastFileLocal"
sed -i "s=//TAG_rainpath=$path=" $model

while [ $step -lt $((duration/period)) ]
do 
  inotifywait -q -q -e modify $RainfallNowcastFileFtp

  timeFile=$(stat --print=%Y ${RainfallNowcastFileFtp})
  if [ $((timeFile-timeLast)) -lt $((period*60)) ] 
  then
    continue
  fi  
  timeLast=$timeFile
  echo "Step ${step}."

  # Remove old data.
  rm $waterLevelFileLocal
  rm $RainfallNowcastFileLocal

  # Copy FTP data to local folder.
  cp $waterLevelFileFtp $waterLevelFileLocal
  cp $RainfallNowcastFileFtp $RainfallNowcastFileLocal

  # Remove time stamps from the retrieved files.
  waterLevelFileContent=$(<$waterLevelFileLocal)
  waterLevel=${waterLevelFileContent#*,}

  while IFS= read -r line; 
  do
   echo ${line#*,}
  done < $RainfallNowcastFileLocal > temp.txt

  mv temp.txt $RainfallNowcastFileLocal

  # Prepare the model.
  cp $modelTemplate $model
  sed -i "s=//TAG_w=$waterLevel=" $model

  # Construct the query.
  final=$(($horizon*$period))

  cat > $query <<EOF
strategy opt = minE (c) [<=$horizon*$period]: <> (t==$final)

simulate [<=$horizon*$period; 1] {PumpSetting} under opt
EOF

  # Execute the queries on the model.
  echo "Start synthesis."
  cmd=$(cat command.txt)
  $cmd $model $query >& $result
  echo "Finished synthesis."

  # Check whether a strategy is synthesized.
  if grep -q "Failed to learn strategy." $result
  then
    echo "No safe strategy synthesized."
    break
  fi

  # Extract control action. We want the control action at the start of the simulation instead of the end.
  tag=$(tail -n 1 ${result})
  # The following analysis assumes we start at 0 for the control state.
  test=${tag#*(} # keep all after first (
  test=${test#*(} # keep all after second (
  test=${test%%)*} # remove everything after )
  time=$(echo ${test} | cut -f 1 -d "," ) # get time of second data point.
  if (( $(echo "$time > 0" |bc -l) )) # if bigger than zero (taking care of possible floats)
  then
    control=0
  else
    control=$(echo ${test} | cut -f 2 -d "," )
  fi
  echo $control > $controlFile
  echo "Submitted new control action."

  step=$((step+1))
done
