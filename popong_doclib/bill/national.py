#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re


def get_lines(text):
    return filter(None,\
        [l.strip('\n') for l in text.split('\n')])

def find_flag(lines, flag):
    for n, l in enumerate(lines):
        if flag.search(l):
            return n
    return None

def get_linefeeds(lines):
    return [n for n, l in enumerate(lines) if l.startswith('')]

def parse(text):
    raise NotImplementedError()

    flag_re = re.compile(r'.*신.*구조문대비표.*')
    page_re = re.compile(r'\s*-\s\d\s-\s*')

    lines = get_lines(text)
    feeds = get_linefeeds(lines)
    flag = find_flag(lines, flag_re)

    # TODO: generalize so that flags may not *exactly* match a page
    flag_idx = feeds.index(flag)
    page = lines[feeds[flag_idx]:feeds[flag_idx+1]][2:]
    colwidth = max(len(re.search(r'\s*', l).group(0)) for l in page) - 7
    for line in page:
        if not page_re.match(line):
            print line[:colwidth]
    print '=============='
    for line in page:
        print line[colwidth:]
