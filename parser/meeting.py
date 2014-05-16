#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import json
import re
import subprocess32 as sp   # only works on POSIX machines

import numpy as np
import regex

import get

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
    return text, nchars

def find_div(text, nchars):
    char_max, char_std = max(nchars), np.std(nchars)
    idx1 = len(nchars) - nchars[::-1].index(char_max)

    for i, t in enumerate(text):
        if re.search(ur'【전자투표\s*찬반\s*의원\s*성명】', t):
            idx2 = i
        if re.search(ur'◯출석\s*의원.*', t):
            idx3 = i
        if re.search(ur'【보고사항】', t):
            idx4 = i

    return [idx1, idx2, idx3, idx4]

def parse_names(row):
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

def parse_dialogue(dialogue):
    parsed = []
    for d in dialogue:
        d = re.sub(r'\s+', ' ', d)
        d = d.strip()
        if any(d.startswith(i) for i in [u'◯']):
            d = '\n\n' + d
        elif any(d.startswith(i) for i in [u'(', u'o']):
            d = '\n' + d
        elif re.match(r'[0-9]+\..*', d):
            d = '\n' + d
        parsed.append(d)
    return ''.join(parsed)

def parse_votes(votes):
    def parse_vote_type(vote_type):
        names = []
        message = []
        for row in vote_type[1:]:
            if regex.fullmatch(ur'(\p{Hangul}|\p{Han}|\s)+', row):
                names.extend(parse_names(row))
            else:
                message.append(row)
        return names, message

    def parse_bill_votes(bill, bill_text):
        idx = []
        votes = {}
        for i, b in enumerate(bill_text):
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
                t = len(bill_text)
            names, message = parse_vote_type(bill_text[s:t])
            votes[attrs[i]] = names
            messages.extend(message)
        bill['votes'] = votes
        bill['message'] = ' '.join(messages)

    idx = [i for i, v in enumerate(votes) if v.startswith(u'◯')]
    votes_in_meeting = []
    for i in range(len(idx)):
        try:
            bill_text = votes[idx[i]:idx[i+1]]
        except IndexError:
            bill_text = votes[idx[i]:]
        bill = {}
        bill['name'] = votes[idx[i]].strip(u'◯')
        parse_bill_votes(bill, bill_text)
        votes_in_meeting.append(bill)
    return votes_in_meeting

def parse_attendance(attendance):
    raise NotImplementedError

def parse_reports(reports):
    raise NotImplementedError

def read_text(filename):
    with open(filename, 'r') as f:
        return f.read().decode('utf-8').split('\n')

def write_text(text, filename):
    with open(filename, 'w') as f:
        f.write(text.encode('utf-8'))

def write_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

if __name__=='__main__':
    directory = '/home/e9t/data/popong/meeting-docs/19/2014-01-01'
    filename = u'19-321-4-본회의.pdf'
    xmlroot = pdf2xml('%s/%s' % (directory, filename))
    text, nchars = get_text(xmlroot)
    idx = find_div(text, nchars)
    print idx

    filebase = filename.replace('.pdf', '')

    dialogue = parse_dialogue(text[idx[0]:idx[1]])
    write_text(dialogue, 'dialogue/%s.txt' % filebase)
    votes = parse_votes(text[idx[1]:idx[2]])
    write_json(votes, 'votes/%s.json' % filebase)
    parse_attendance(text[idx[2]:idx[3]])
    #parse_reports(text[idx[3]:])
