#!/bin/bash

path_in="../tests/data/tagesschau-mini.vrt.gz"

corpus_name="TAGESSCHAU-MINI"

registry_dir="/usr/local/share/cwb/registry/"
data_dir="/usr/local/share/cwb/data/"

registry_file="$registry_dir${corpus_name,,}"
data_subdir="$data_dir${corpus_name,,}"

echo "data directory: $data_subdir"
mkdir -p $data_subdir

echo "cwb-encode (registry file: $registry_file)"
cwb-encode -d $data_subdir -f $path_in -R "$registry_file" -xsBC -c utf8 -9 -P pos -S article:0+date+fname+month+rubrik+year -S p:0+type -S s:0

echo "cwb-make"
cwb-make -r $registry_dir -M 4096 -V "$corpus_name"
