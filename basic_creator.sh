#!/usr/bin/env bash

# Exit immediately if a simple command exits with a non-zero status.
set -e

function usage () {
   cat <<EOF
Usage: $0 [-e <executable>] -i <input> -o <output> -c <collect>
where:
    -i <in_path> path to input
    -o <out_path> path where workspaces should be created
    -c <type> collect type
    -e <exec> you can choose your binary to generate workspaces
Program will generate 100 different workspaces.
Each of them will have different number of particles and
threads.
EOF
   exit 0
}

INPUT=""
OUTPUT=""
COLLECT=""
EXECUTABLE=generatemc

while getopts ":i:o:c:m:e:" opt; do
  case $opt in
    e)
      EXECUTABLE=$OPTARG
      ;;
    c)
      COLLECT=$OPTARG
      ;;
    i)
      INPUT=$OPTARG
      ;;
    o)
      OUTPUT=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      exit 1
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

if [[ $INPUT == "" ]] || [[ $OUTPUT == "" ]] || [[ $COLLECT == "" ]] ; then
    echo -e "\n Make sure you have passed arguments correctly\n"
    usage
fi 

echo "EXECUTABLE=$EXECUTABLE INPUT=$INPUT OUTPUT=$OUTPUT COLLECT=$COLLECT"
mkdir -p $OUTPUT
START_PATH=$PWD
cd $OUTPUT
for k in {1..3}
do
PART=4000000000
sleep 2
    for i in {1..18}
    do
        PART=$(($PART / 2))
        echo "Creating workspaces with $PART particles"
        mkdir -p "particles_$PART"
        for THREADS in 10 50 100 175 250 325 400 475 550 625 700 775
        do
            mkdir -p "particles_$PART/threads_$THREADS"
            ../$EXECUTABLE -j $THREADS -p $(($PART / $THREADS)) ../$INPUT -w particles_$PART/threads_$THREADS -c $COLLECT -s "[ --time=30:00:00]"
            #mkdir -p particles_$PART/threads_$THREADS/${k}_th_${THREADS}_part_$((PART / $THREADS))_in_${INPUT}_out_${OUTPUT}_cl_$COLLECT
        done
    done
done
cd $START_PATH




