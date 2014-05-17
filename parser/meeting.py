#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from itertools import groupby
import json
import os
import re
import subprocess32 as sp   # only works on POSIX machines

import numpy as np
import regex

import get

def get_filenames(basedir):
    os.chdir(basedir)
    return [os.path.join(path, name).decode('utf-8')\
            for path, subdirs, files in os.walk('.')\
                for name in files]

def pdf2xml(pdffile):
    sp.check_output(['pdftohtml', '-c', '-q', '-xml', pdffile])
    xmlfile = pdffile.replace('.pdf', '.xml')
    xmlroot = get.localtree(xmlfile)
    sp.check_call(['rm', xmlfile])
    return xmlroot

def get_text(xmlroot):
    textelems = []
    pages = xmlroot.xpath('//page')
    for i, page in enumerate(pages):
        elems = page.xpath('.//text')
        if not i==0:
            elems = elems[1:]
        textelems.extend(elems)
    text = [e.xpath('./text()')[0] for e in textelems]
    nchars = [int(e.xpath('./@width')[0]) for e in textelems]
    linenum = [int(e.xpath('./@top')[0]) for e in textelems]
    return text, nchars, linenum

def find_div(text, nchars):
    idx = {}
    char_max, char_std = max(nchars), np.std(nchars)
    idx[len(nchars) - nchars[::-1].index(char_max)] = 'dialogue'

    for i, t in enumerate(text):
        if re.search(ur'【전자투표\s*찬반\s*의원\s*성명】', t):
            idx[i] = 'votes'
        if re.search(ur'◯출석\s*(의|위)원.*', t):
            idx[i] = 'attendance'
        if re.search(ur'【보고사항】', t):
            idx[i] = 'reports'
    return idx

def chunk(items, idx, i):
    # i: start index
    try:
        return items[idx[i]:idx[i+1]]
    except IndexError:
        return items[idx[i]:]

def chunk_all(items, idx):
    return [chunk(items, idx, i) for i in range(len(idx))]

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
        if any(d.startswith(i) for i in [u'◯']):
            d = '\n\n' + d
        elif any(d.startswith(i) for i in [u'(', u'o']):
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

        attrs = ['yes', 'nay', 'forfeit']
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
    idx = [i for i, v in enumerate(votes) if v.startswith(u'◯')]
    chunks = chunk_all(votes, idx)
    for i in range(len(idx)):
        bill = {}
        bill['name'] = votes[idx[i]].strip(u'◯')
        parse_bill_text(bill, chunks[i])
        votes_in_meeting.append(bill)
    return votes_in_meeting

def parse_attendance(attendance, linenum):
    # TODO: enhance 'special types' parsing performance
    def parse_chunk(c, l):
        d = {}
        desc = c[0].strip(u'◯').split('(')
        if len(desc)==1:
            count = None
        else:
            count = int(re.search(r'[0-9]+', desc[1]).group(0))
        d[desc[0].strip()] = {
            'count': count,
            'names': parse_names(c[1:], l[1:])[0]
            }
        return d

    idx = [i for i, a in enumerate(attendance) if a.startswith(u'◯')]
    cz = chunk_all(attendance, idx)
    lz = chunk_all(linenum, idx)
    return filter(None, [parse_chunk(c, l) for c, l in zip(cz, lz)])

def parse_reports(reports):
    raise NotImplementedError

def check_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_text(filename):
    with open(filename, 'r') as f:
        return f.read().decode('utf-8').split('\n')

def write_text(text, filename):
    check_dir(os.path.dirname(filename))
    with open(filename, 'w') as f:
        f.write(text.encode('utf-8'))

def write_json(data, filename):
    check_dir(os.path.dirname(filename))
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def parse_meeting(datafile, basedir):
    filebase = datafile.replace('.pdf', '')[2:]
    xmlroot = pdf2xml(datafile)
    text, nchars, linenum = get_text(xmlroot)
    div = find_div(text, nchars)
    tmp = sorted(div.items(), key=lambda x: x[0])
    indexes = [t[0] for t in tmp]
    types = [t[1] for t in tmp]

    for i in range(len(div)):
        if types[i]=='dialogue':
            dialogue = parse_dialogue(chunk(text, indexes, i))
            write_text(dialogue, '%s/dialogue/%s.txt' % (basedir, filebase))
        elif types[i]=='votes':
            votes = parse_votes(chunk(text, indexes, i))
            write_json(votes, '%s/votes/%s.json' % (basedir, filebase))
        elif types[i]=='attendance':
            attendance = parse_attendance(chunk(text, indexes, i),\
                    chunk(linenum, indexes, i))
            write_json(attendance, '%s/attendance/%s.json' % (basedir, filebase))

    # TODO: parse_reports(text[indexes[3]:])


if __name__=='__main__':
    basedir = '/home/e9t/data/popong'
    pdfdir = '%s/meeting-docs' % basedir
    meetingdir = '%s/meeting-data' % basedir

    filenames = get_filenames(pdfdir)
    for i, filename in enumerate(filenames):
        print filename
        filebase = filename.replace('.pdf', '')[2:]
        dialoguefile = '%s/dialogue/%s.txt' % (meetingdir, filebase)
        if not os.path.isfile(dialoguefile):
            parse_meeting(filename, meetingdir)
