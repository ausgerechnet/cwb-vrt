#!/bin/bash

path_in="tests/data/tagesschau-mini.vrt.gz"

corpus_name="TAGESSCHAU-MINI"

registry_dir="/usr/local/share/cwb/registry/"
data_dir="/usr/local/share/cwb/data/"

registry_file="$registry_dir${corpus_name,,}"
data_subdir="$data_dir${corpus_name,,}"

echo "data directory: $data_subdir"
mkdir -p $data_subdir

echo "cwb-encode (registry file: $registry_file)"
cwb-encode -d $data_subdir -f $path_in -R "$registry_file" -xsBC -c utf8 -9 -P pos -S corpus:0 -S article:0+date+fname+month+rubrik+year -S p:0+type -S s:0

echo "cwb-make"
cwb-make -r $registry_dir -M 4096 -V "$corpus_name"

echo "lemmatisation"
cwb-lemmatize-smor -E -T $corpus_name

echo "export"
file_out="tests/data/tagesschau-mini-lemma.vrt"
cwb-decode -Cx $corpus_name -P word -P pos -P lemma -S corpus:0 -S article:0+date+fname+month+rubrik+year -S p:0+type -S s:0 > $file_out

echo "compressing"
gzip $file_out
