#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import string
import unicodedata
import xml.etree.ElementTree as ET
from html import escape, unescape


def unescape_multiply_escaped(text, escape_chars={"&amp;", "&lt;", "&gt;", "&quot;", "&apos;"}):
    """unescapes (potentially) multiply XML-escaped string into normally escaped string.

    """

    while any(x in text for x in escape_chars):
        text = unescape(text)

    return escape(text)


def escape_xml_mysql(text):
    """escape certain characters so that string does not contain any characters beyond the mbp,
    which is required by MySQL's utf8 collation (which is not utf8mb4) as of CQPweb 3.2.31

    https://stackoverflow.com/questions/13729638/how-can-i-filter-emoji-characters-from-my-input-so-i-can-save-in-mysql-5-5/13752628#13752628

    """

    try:
        # UCS-4
        highpoints = re.compile(u'[\U00010000-\U0010ffff]')
    except re.error:
        # UCS-2
        highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    text = highpoints.sub(u'\u25FD', text)

    return text


def force_categorical(text, fallback="NA"):
    """converts strings to valid CQPweb categorical variables

    """

    # these characters are safe to use in CQPweb
    whitelist = set(
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789'
    )

    # some common German transliterations
    text = re.sub("ä", "ae", text)
    text = re.sub("Ä", "AE", text)
    text = re.sub("ö", "oe", text)
    text = re.sub("Ö", "OE", text)
    text = re.sub("ü", "ue", text)
    text = re.sub("Ü", "UE", text)
    text = re.sub("ß", "ss", text)

    # replace common separators with underscores
    text = re.sub(" ", "_", text)
    text = re.sub("/", "_", text)
    text = re.sub("-", "_", text)
    text = re.sub(r"\|", "_", text)

    # normalize (Asian spelling ...)
    text = ''.join(x for x in unicodedata.normalize('NFKD', text) if x in string.printable).lower()

    # remove everything except whitelisted characters
    handle = ''.join(filter(whitelist.__contains__, text))

    # use fallback for empty strings
    handle = fallback if handle == "" else handle

    if not re.search("^[A-Za-z]", handle):
        handle = "c_" + handle

    return handle


def meta2dict(line, level='text'):
    """converts .vrt meta data line into dictionary

    """

    line = re.sub("&", "&amp;", line)  # allow ampersands in input
    tree = ET.fromstring(line + "</" + level + ">")  # close tag

    # create dictionary
    out = dict()
    for el in tree.items():
        out[el[0].strip()] = el[1].strip()

    return out


def dict2meta(d, index_key='id', level='text'):
    """converts dictionary into .vrt meta data line

    """

    line = f'<{level}'

    # make sure index is the first one
    if index_key is not None:
        idx = d.pop(index_key)
        line += f' id="{idx}"'

    for k in d.keys():
        line += f' {k}="{d[k]}"'

    # revert modification of original input
    if index_key is not None:
        d[index_key] = idx

    return line + ">\n"


def remove_whitespace(txt):
    """remove newlines, carriage returns, and tabulators

    """

    if type(txt) is str:
        txt = txt.replace("\n", " ")
        txt = txt.replace("\r", " ")
        txt = txt.replace("\t", " ")

    return txt
