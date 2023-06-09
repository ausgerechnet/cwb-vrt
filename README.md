# cwb-vrt #
**cwb-vrt** is a Python 3 module and command line interface for processing VRT files.

VRT files are XML files containing verticalised text and are used as an import (and export) format of the [IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).  The CWB distinguishes **positional attributes** (p-atts) on a token-level, which are stored in tab-separated lines, and **structural attributes** (s-atts) stored in XML elements (i.e. matching pairs of start and end tags).
```
<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>
<!-- A Thrilling Experience -->
<story num="4" title="A Thrilling Experience">
<p>
<s>
Tick	NN	tick
.	SENT	.
</s>
<s>
A	DT	a
clock	NN	clock
.	SENT	.
</s>
<s>
Tick	VB	tick
,	,	,
tick	VB	tick
.	SENT	.
</s>
</p>
...
</story>
...
```
The VRT file above contains three p-atts: by default, the first or *primary* layer is called `word` — the other p-atts here would be `pos` and `lemma`. Note that the names of p-atts are usually not explicitly encoded in VRT files.

There are also three s-atts (`story`, `p`, and `s`). The XML-element `story` has two attribute-value pairs:
```
<story num="4" title="A Thrilling Experience">
```
cwb-vrt usually refers to the name of the XML element (e.g. `story`) as "level" of the s-att. Note that in the CWB, each attribute-value pair will be stored as a separate s-att (here: `story_num` and `story_title`) with **annotation**.  `p` and `s` do not have any annotation.

## Installation ##

```
pip install git+ssh:git@github.com/ausgerechnet/cwb-vrt.git
```

## Using the CLI

`vrt-cohort`: conflate texts according to meta data into cohorts
```
vrt-cohort -m tagesschau-mini.vrt.gz -c month rubrik --level-old article --level-new article
```

`vrt-cqpweb`: make VRT file compatible with CQPweb
```
vrt-cqpweb tagesschau-mini.vrt.gz --level article
```

`vrt-deduplicate`: check regions enclosed by level for duplicates
```
vrt-deduplicate tagesschau-mini.vrt.gz --level s
```

`vrt-index`: create CWB import script from VRT file
```
vrt-index tagesschau-mini.vrt.gz
  ```

`vrt-meta`: create TSV table of meta data stored in s-atts
```
vrt-meta tagesschau-mini.vrt.gz --level article
```
