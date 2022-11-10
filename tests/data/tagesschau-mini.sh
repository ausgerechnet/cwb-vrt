#!/bin/bash

path_in="tests/data/tagesschau-mini.vrt.gz"
corpus_name="TAGESSCHAU-MINI"
registry_file="/usr/local/share/cwb/registry/tagesschau-mini"
data_dir="/usr/local/share/cwb/data/tagesschau-mini"
registry_dir="/usr/local/share/cwb/registry/"

echo "create data directory"
mkdir -p $data_dir

echo "cwb-encode"
cwb-encode -d $data_dir -f $path_in -R "$registry_file" -xsB -c utf8 -P pos -S corpus -S article:0+date+fname+month+rubrik+year -S p:0+type -S s

echo "cwb-make"
cwb-make -r $registry_dir -M 4096 -V "$corpus_name"

echo "lemmatisation"
cwb-lemmatize-smor -E -T $corpus_name

echo "export"
file_out="tests/data/tagesschau-mini-lemma.vrt"
cwb-decode -Cx $corpus_name -P word -P pos -P lemma -S article:0+date+fname+month+rubrik+year -S p:0+type -S s > $file_out

echo "compressing"
gzip $file_out
