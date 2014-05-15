#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re


def get_lines(fname):
    with open(fname, 'r') as f:
        return filter(None,\
                [l.decode('utf-8').strip('\n') for l in f.readlines()])

def find_flag(lines, flag):
    for n, l in enumerate(lines):
        if flag.search(l):
            return n
    return None

def get_linefeeds(lines):
    return [n for n, l in enumerate(lines) if l.startswith('')]

def parse(bill_num):
    fname = 'results/%d.txt' % bill_num
    flag_re = re.compile(r'.*신.*구조문대비표.*')
    page_re = re.compile(r'\s*-\s\d\s-\s*')

    lines = get_lines(fname)
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

if __name__=='__main__':
    import sys
    from_, to_ = map(int, sys.argv[1:3])
    #for n in range(1904880, 1904881):
    for n in range(from_, to_):
        print '#%d-------------------------------------------------------' % n
        parse(n)
