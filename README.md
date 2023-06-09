# cwb-vrt #
A python module and command line utility for processing VRT files.

VRT is used as an import (and export) format of the [IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).  VRT files are XML files containing verticalised text.  The CWB distinguishes **positional attributes** (p-atts) on a token-level, which are stored in tab-separated lines, and **structural attributes** (s-atts) stored in XML elements (i.e. matching pairs of start and end tags).
```
<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>
<!-- A Thrilling Experience -->
<story num="4" title="A Thrilling Experience">
<p>
<s>
Tick
NN
tick
.
SENT
.
</s>
<s>
A
DT
a
clock
NN
clock
.
SENT
.
</s>
<s>
Tick
VB
tick
,
,
,
tick
VB
tick
.
SENT
.
</s>
</p>
...
</story>
...
```


The VRT file above containes three s-atts (`story`, `p`, `s`) and one p-att (by default, the first or *primary* layer is called `word`). The XML-element `story` has two attribute-value pairs:
```
<story num="4" title="A Thrilling Experience">
```
cwb-vrt usually refers to the name of the XML element (`story`) as "level" of the s-att.


## usage of the command line utility

- `vrt-cohort`: conflate texts according to meta data into cohorts
  ```
  vrt-cohort -m tagesschau-mini.vrt.gz -c month rubrik --level-old article --level-new article
  ```

- `vrt-cqpweb`: make VRT file compatible with CQPweb
  ```
  vrt-cqpweb tagesschau-mini.vrt.gz --level article
  ```

- `vrt-deduplicate`: check regions enclosed by level for duplicates
  ```
  vrt-deduplicate tagesschau-mini.vrt.gz --level s
  ```

- `vrt-index`: create CWB import script from VRT file
  ```
  vrt-index tagesschau-mini.vrt.gz
  ```

- `vrt-meta`: create tsv table of meta data stored in s-atts
  ```
  vrt-meta tagesschau-mini.vrt.gz --level article
  ```


## installation ##

```
pip install .
```

## testing ##


## VRT creation ##
