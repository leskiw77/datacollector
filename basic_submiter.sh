#!/usr/bin/env bash

function usage () {
   cat <<EOF
Usage: $0 -i <directory>
where:
    -i <path> path to directory with workspaces
EOF
   exit 0
}

INPUT=""

while getopts ":i:" opt; do
  case $opt in
    i)
      INPUT=$OPTARG
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

if [[ $INPUT == "" ]] ; then
    echo -e "\n Make sure you have passed arguments correctly\n"
    usage
fi 


echo "INPUT=$INPUT"
LIMIT=820
START_PWD=$PWD
cd $INPUT
for PART_DIR in *
do
    echo $PART_DIR
    cd $PART_DIR
    for TH_DIR in *
    do
        echo -e "\t$TH_DIR"
        THREADS=$(echo $TH_DIR | sed 's/[^0-9]*//g')
        echo -e "\tWorking for $THREADS threads"
        cd $TH_DIR
        for RUN_DIR in *
        do
             echo -e "\t\t$RUN_DIR"
             cd $RUN_DIR
                 SQUEUE=$(squeue)
                 while [[ $SQUEUE = *"]"*  ]] ; do
                     echo -e "\t\t\tWaiting for all jobs to be in running state"
                     sleep 15
                     SQUEUE=$(squeue)
                 done
                 NR_JOBS=$(squeue | wc -l)
                 echo -e "\t\t\tThere are $(($NR_JOBS - 1)) jobs running"
                 SUM=$(((NR_JOBS - 1 ) + $THREADS))
                 echo -e "\t\t\tBut we want to run next $THREADS so sum=$SUM"
                 while [ $SUM -gt $LIMIT ] ; do
                     echo -e "\t\t\tTo many jobs would be lunched, have to wait for some jobs to finish.."
                     sleep 120
                     NR_JOBS=$(squeue | wc -l)
                     echo -e "\t\t\tThere are $(($NR_JOBS - 1)) jobs running"
                     SUM=$(((NR_JOBS - 1 ) + $THREADS))
                     echo -e "\t\t\tBut we want to run next $THREADS so sum=$SUM"
                 done
             
             out=$(./submit.sh)
             echo -e "\t\t\t$out"
             echo -e "\t\t\tSubmited for $RUN_DIR"
             cd ..
        done
        cd ..
    done
    cd ..
done

cd $START_PWD




