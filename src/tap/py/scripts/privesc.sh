#!/bin/bash


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

        sudo setcap cap_net_raw,cap_net_admin=eip $program
        ;;
    unset | rm | del)
        sudo setcap -r $program

        if [ -f $ogcap_file ]
        then
            caps=$(cat $ogcap_file | tr '\n' ',')
            if [[ -z "${caps}" ]]
            then
                echo "had no capabilities set before"
            else
                sudo setcap $caps $program
            fi
        fi
        ;;
    *)
        echo "you muppet, pass an arg"
        exit 2
        ;;
esac
