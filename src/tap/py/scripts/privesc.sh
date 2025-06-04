#!/bin/bash


# Disclaimer: this is not an actual privilege escalation script
# it just assigns networking capabilities (which is also powerful, but...)

program=${2:-"/usr/bin/python3.12"}
progname=$(echo "${program//// }" | tr ' ' '_')
ogcap_file="ogcap-$progname.tmp"

case $1 in
    get)
        echo "$program capabilities: "
        getcap $program
        ;;
    set)
        getcap $program | awk '{print $2}' | tr -d '[:space:]' > $ogcap_file

        setcap cap_net_raw,cap_net_admin=eip $program
        ;;
    unset | rm | del)
        setcap -r $program

        if [ -f $ogcap_file ]
        then
            caps=$(cat $ogcap_file | tr '\n' ',')
            if [[ -z "${caps}" ]]
            then
                echo "had no capabilities set before"
            else
                setcap $caps $program
            fi
        fi
        ;;
    *)
        echo "you muppet, pass an arg"
        exit 2
        ;;
esac
