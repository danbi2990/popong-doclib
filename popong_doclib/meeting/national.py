#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from itertools import groupby
import os
import re

import numpy as np
import regex

from dialogue import txt2html, txt2json
from .. import utils

BIGO = u'◯'
LITTLEO = u'o'

def find_div(text, nchars):
    for i, t in enumerate(text):
        if re.search(ur'\([0-9]+시\s*[0-9]+분\s*(개의|개회|개식|개시)\)', t):
            idx[i] = 'dialogue'
        if re.search(ur'【전자투표\s*찬반\s*의원\s*성명】', t):
            idx[i] = 'votes'
        if re.search(ur'◯(출|참)석\s*(감사위|의|위)원.*', t):
            idx[i] = 'attendance'
        if re.search(ur'【보고사항】', t):
            idx[i] = 'reports'
    tmp = sorted(idx.items(), key=lambda x: x[0])
    indexes = [t[0] for t in tmp]
    types = [t[1] for t in tmp]
    return indexes, types

def parse_names(rows, linenum=None):
    # FIXME: buggy
    def groupby_linenum(rows, linenum):
        return ['\t'.join(g[0] for g in list(group))\
            for i, group in groupby(zip(rows, linenum), lambda x: x[1])]

    def _parse_names(row):
        names = [re.sub('\s', '', name)\
                for name in row.strip().split('   ')]
        for i, name in enumerate(names[:-1]):
            name = names[i]
            next_name = names[i+1]
            to_del = []
            if len(name)==1 and len(next_name)==1:
                names[i] = '%s%s' % (name, next_name)
                names[i+1] = ''
        return filter(None, names)

    names = []
    message = []
    if linenum:
        rows = groupby_linenum(rows, linenum)
    for row in rows:
        if regex.fullmatch(ur'(\p{Hangul}|\p{Han}|\s|[0-9])+', row):
            names.extend(_parse_names(row))
        else:
            message.append(row)
    return names, message

def parse_dialogue(dialogue):
    parsed = []
    for d in dialogue:
        d = re.sub(r'\s+', ' ', d)
        if any(d.startswith(i) for i in [BIGO]):
            d = '\n\n' + d
        elif any(d.startswith(i) for i in [LITTLEO]):
            d = '\n' + d
        elif re.match(ur'\([0-9]+시\s*[0-9]+분\)', d):
            d = '\n' + d
        elif re.match(r'[0-9]+\..*', d):
            d = '\n' + d
        parsed.append(d)
    return ''.join(parsed)

def parse_votes(votes):
    def parse_bill_text(bill, text):
        idx = []
        votes = {}
        for i, b in enumerate(text):
            if re.search(ur'.*찬성\s*의원\s*\(.*\).*', b):
                idx.append(i)
            if re.search(ur'.*반대\s*의원\s*\(.*\).*', b):
                idx.append(i)
            if re.search(ur'.*기권\s*의원\s*\(.*\).*', b):
                idx.append(i)

        attrs = ['yea', 'nay', 'forfeit']
        messages = []
        for i in range(len(idx)):
            s = idx[i]
            try:
                t = idx[i+1]
            except IndexError:
                t = len(text)
            names, message = parse_names(text[s:t])
            votes[attrs[i]] = names
            messages.extend(message)
        bill['votes'] = votes
        bill['message'] = ' '.join(messages)

    votes_in_meeting = []
    idx = [i for i, v in enumerate(votes) if v.startswith(BIGO)]
    chunks = utils.chunk_all(votes, idx)
    for i in range(len(idx)):
        bill = {}
        bill['name'] = votes[idx[i]].strip(BIGO)
        parse_bill_text(bill, chunks[i])
        votes_in_meeting.append(bill)
    return votes_in_meeting

def parse_attendance(attendance, linenum):
    # TODO: enhance 'special types' parsing performance
    d = {}
    def parse_chunk(c, l):
        desc = c[0].strip(BIGO).split('(')
        if len(desc)==1:
            count = None
        else:
            count = int(re.search(r'[0-9]+', desc[1]).group(0))
        d[desc[0].strip()] = {
            'count': count,
            'names': parse_names(c[1:], l[1:])[0]
            }

    idx = [i for i, a in enumerate(attendance) if a.startswith(BIGO)]
    cz = utils.chunk_all(attendance, idx)
    lz = utils.chunk_all(linenum, idx)
    for c, l in zip(cz, lz):
        parse_chunk(c, l)
    return d

def parse_reports(reports):
    raise NotImplementedError

def make_filenames(pdffile, ext='.pdf'):
    filebase = pdffile.replace(ext, '')[2:]
    fn = {
        'attendance': '%s/attendance/%s.json' % (datadir, filebase),
        'dialogue_txt': '%s/dialogue/%s.txt' % (datadir, filebase),
        'dialogue_html': '%s/dialogue/%s.html' % (datadir, filebase),
        'dialogue_json': '%s/dialogue/%s.json' % (datadir, filebase),
        'votes': '%s/votes/%s.json' % (datadir, filebase),
    }
    return fn

def get_sections(xmlroot):
    textelems = utils.get_textelems(xmlroot)
    text = [e.xpath('./text()')[0] for e in textelems]
    nchars = [int(e.xpath('./@width')[0]) for e in textelems]
    # linenum = [int(e.xpath('./@top')[0]) for e in textelems]
    indexes, types = find_div(text, nchars)
    chunks = [utils.chunk(textelems, indexes, i) for i in range(len(indexes))]
    return [{"type": types[i], "starts_at": indexes[i], "elems": chunks[i]}\
            for i in range(len(chunks))]

def parse_all(sections):
    all_ = {}
    for section in sections:
        text = [e.xpath('./text()')[0] for e in section['elems']]

        if section['type']=='dialogue':
            dialogue_txt = parse_dialogue(text)
            dialogue_html = txt2html(dialogue_txt)
            dialogue_json = txt2json(dialogue_txt)
            # utils.write_text(dialogue_txt, fn['dialogue_txt'])
            # utils.write_text(dialogue_html, fn['dialogue_html'])
            # utils.write_json(dialogue_json, fn['dialogue_json'])
            all_[section['type']] = dialogue_json
        elif section['type']=='votes':
            votes = parse_votes(text)
            all_[section['type']] = votes
            # utils.write_json(votes, fn['votes'])
        elif section['type']=='attendance':
            lines = [int(e.xpath('./@top')[0]) for e in section['elems']]
            attendance = parse_attendance(text, lines)
            all_[section['type']] = attendance
            # utils.write_json(attendance, fn['attendance'])
        elif section['type']=='reports':
            # TODO: parse_reports(text[indexes[3]:])
            all_[section['type']] = None
        else:
            raise Exception('Invalid section type "%s"' % section['type'])

    return all_
