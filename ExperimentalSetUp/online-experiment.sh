#!/usr/bin/env bash

# Get the value of a variable from a file.
function getValue() {
    file=$1
    var=$2
    grep "^$var =" $file | gawk '{ print $3 }'
}

# Get the integer value of a variable from a file.
function getIntValue() {
    file=$1
    var=$2
    value=$(getValue $file $var)
    echo ${value%.*}
}

# 1d = 24h, 2d = 48h, 3d = 72h.

# Period in time units (minutes).
period=60
# How many periods to compute strategy for.
horizon=24
# Duration of experiment in periods.
duration=72

# Overall data collection.
data="trajectory.txt"

# Define variables to collect.
step=0
lastTime="0.0"
lastW="100.0"
lastQout="0.0"
lastD="0.0"
lastRain="0.0"
lastRainLoc="0"
lastI="0"
lastSUC="0.0"
lastC="0.0"
lastO="0.0"
nvar=10

echo "step t w qout d rain RainLoc i S_UC c o stratego-time stratego-memory" > $data
echo "$step $lastTime $lastW $lastQout $lastD $lastRain $lastRainLoc $lastI $lastSUC $lastC $lastO 0.0 0" >> $data

while [ $step -lt $duration ]
do      
    # Define file names for this step.
    model="model-$step.xml"
    resource="resource-$step.log"
    result="result-$step.log"
    state="state-$step.log"
    control="control-action-$step.log"
    query=query-$step.q

    # Adjust model for this time step.
    cp ../../pond_ADHS_online.xml $model
    sed -i "s/clock t = 0.0;/clock t = $lastTime;/" $model
    sed -i "s/clock w = 100.0;/clock w = $lastW;/" $model
    sed -i "s/clock d = 0.0;/clock d = $lastD;/" $model
    sed -i "s/double rain = 0.0;/double rain = $lastRain;/" $model
    sed -i "s/int rainLoc = 0;/int rainLoc = $lastRainLoc;/" $model
    sed -i "s/clock S_UC = 0.0;/clock S_UC = $lastSUC;/" $model
    sed -i "s/int i = 0;/int i = $lastI;/" $model
    sed -i "s/clock c = 0.0;/clock c = $lastC;/" $model
    
    # Adjust query for this time step.
    offset=${lastTime%.*}
    final=$(($horizon*$period+$offset))
    cat > $query <<EOF
strategy opt = minE (c) [<=$horizon*$period]: <> (t==$final && o <= 0)

simulate 1 [<=$period+1] {t, w, Qout, Rain.d, rain, Rain.rainLoc, Rain.i, S_UC, c, o} under opt
EOF

    # Execute the queries on the model.
    cmd=$(cat command.txt)
    /usr/bin/time -f "%U %M" --output $resource $cmd $model $query >& $result
    
    # Check whether a strategy is synthesized.
    if grep -q "Failed to learn strategy." $result
    then
	echo "No safe strategy synthesized at step $step."
	echo "Synthesizing strategy for minimal water level."
	cat > $query <<EOF
strategy opt = minE (w) [<=$horizon*$period]: <> (t==$final)

simulate 1 [<=$period+1] {t, w, Qout, Rain.d, rain, Rain.rainLoc, Rain.i, S_UC, c, o} under opt
EOF
	# Execute the queries on the model.
	cmd=$(cat command.txt)
	/usr/bin/time -f "%U %M" --output $resource $cmd $model $query >& $result
    fi
    
    # Extract state after simulating a single period.
    # The value of n should be double the number of variables to be extracted.
    tail -n $((2*nvar)) $result | ../../extract-state > $state
    lastTime=$(getValue $state t)
    lastW=$(getValue $state w)
    lastD=$(getValue $state Rain.d)
    lastRain=$(getValue $state rain)
    lastRainLoc=$(getIntValue $state Rain.rainLoc)
    lastI=$(getIntValue $state Rain.i)
    lastSUC=$(getValue $state S_UC)
    lastC=$(getValue $state c)
    lastO=$(getValue $state o)
    lastRes=$(cat $resource)
    step=$((step+1))

    # Extract control action. We want the control action at the start of the simulation instead of the end.
    tail -n $((2*nvar)) $result | ../../extract-control-action > $control
    lastQout=$(getValue $control Qout)
    echo "$step $lastTime $lastW $lastQout $lastD $lastRain $lastRainLoc $lastI $lastSUC $lastC $lastO $lastRes" >> $data
done
      

