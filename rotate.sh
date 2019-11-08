#!/bin/bash
# Rotate Log
script=$(readlink -f "$0")
base=$(dirname "$script")
file=ERROR.txt
compressfile=ERROR.tar.gz
minimumsize=10000000
if [ -f "$base/$file" ]; then
	actualsize=$(wc -c < "$base/$file")
	if [ $actualsize -ge $minimumsize ]; then
		if [ -f "$base/$compressfile" ]; then
			rm -r $base/$compressfile
		fi
		tar -czvf $base/$compressfile $base/$file
		rm -r "$base/$file"
	fi
fi
