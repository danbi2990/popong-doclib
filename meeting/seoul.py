#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
from glob import glob

from BeautifulSoup import BeautifulSoup
from lxml.etree import fromstring, tostring

from dialogue import txt2json
import get
import utils

def get_dialogue_indexes(times):
    text = [t[1] for t in times]
    opening = [u'개의', u'개회', u'개식', u'개시']
    closing = [u'폐의', u'폐회', u'폐식', u'산회', u'24시', u'종료']

    start, end = None, None
    for i, t in enumerate(text):
        if any((i in t) for i in opening):
            start = times[i][0]
        if any((i in t) for i in closing):
            end = times[i][0] + 1

    if not start:
        start = times[0][0]
        print '\tcheck this file for starting point'
    if not end:
        end = times[-1][0] + 1
        print '\tcheck this file for ending point'
    return (start, end)

def get_elems(htmlfile):
    def _get_elems(page):
        return page.findall('.//')
    with open(htmlfile, 'r') as f:
        soup = BeautifulSoup(f)
    html = soup.prettify()
    root = get.texttree(html)
    pages = root.xpath('//page')
    elems = sum((_get_elems(page) for page in pages), [])
    return elems

def get_tail(elem):
    return elem.tail.strip()

def get_text(elem):
    return ' '.join(q.strip() for q in elem.xpath('.//text()'))

def get_times(elems):
    times = []
    for i, elem in enumerate(elems):
        if elem.tag=='div' and elem.attrib['class']=='r':
            times.append([i, elem.xpath('.//text()')[0].strip()])
    return times

def parse_dialogue(dialogue):
    def parse_elem(elem):
        if elem.tag=='b':
            p = '%s %s' % (get_text(elem), get_tail(elem))
            p = '\n' + p.strip()
        elif elem.tag=='div':
            p = '\n' + get_text(elem) + '\n'
        elif elem.tag in ['br', 'hr']:
            p = get_tail(elem)
        else:
            p = ''
        return p

    d = [parse_elem(elem) for elem in dialogue if not elem.tag=='a']
    return ''.join(d)

def parse_others(elems):
    def get_title(i):
        t = elems[i+1].xpath('.//text()')
        if t:
            t = t[0]
        else:
            t = elems[i].tail
        return t.strip()

    def find_div(elems):
        indexes = [i for i, line in enumerate(elems) if line.tag=='hr']
        types = []
        for i in indexes:
            title = get_title(i)
            if u'참조' in title:
                types.append('appendix')
            if u'투표' in title:
                types.append('votes')
            if u'출석' in title:
                types.append('attendance')
        tmp = zip(indexes, types)
        indexes = [t[0] for t in tmp]
        types = [t[1] for t in tmp]
        return indexes, types

    def tohtml(elems):
        return '\n'.join(tostring(line) for line in elems if not\
            (line.tag in ['tbody', 'tr', 'td'] or line.getparent().tag=='td'))

    indexes, types = find_div(elems)
    others = {}
    for i in range(len(indexes)):
        chunk_elems = utils.chunk(elems, indexes, i)
        others[types[i]] = tohtml(chunk_elems)
    return others


if __name__=='__main__':
    basedir = '.'
    basedir = '/home/e9t/data/popong'
    htmldir = '%s/meeting-docs/seoul' % basedir

    htmlfiles = [h for h in utils.get_filenames(htmldir) if h.endswith('.html')]
    for h in htmlfiles:
        filebase = h[2:].replace('.html', '')
        htmlfile = '%s/meeting-docs/seoul/%s.html' % (basedir, filebase)
        textfile = '%s/meetings/seoul/dialogue/%s.txt' % (basedir, filebase)
        jsonfile = '%s/meetings/seoul/dialogue/%s.json' % (basedir, filebase)
        print htmlfile

        if not os.path.isfile(textfile):
            elems = get_elems(htmlfile)
            times = get_times(elems)
            s, e = get_dialogue_indexes(times)

            dialogue = elems[s:e]
            others = elems[e:]

            # parse dialogue
            dialogue_txt = parse_dialogue(dialogue)
            dialogue_json = txt2json(dialogue_txt)
            utils.write_text(dialogue_txt, textfile)
            utils.write_json(dialogue_json, jsonfile)

            # parse others (attendance, votes, appendix)
            others = parse_others(others)
            for k, v in others.items():
                utils.write_text(v,\
                    '%s/meetings/seoul/%s/%s.html' % (basedir, k, filebase))
