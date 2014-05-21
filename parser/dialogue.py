#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import re
import utils


startsignal = u'◯'

def parse_speech(line):
    words = line.strip(startsignal).split()
    speaker = words[:2]
    speech = words[2:]
    return speaker, speech

def txt2html(txt):

    html = []
    for line in filter(None, txt.split('\n')):
        if line.startswith(startsignal):
            speaker, speech = parse_speech(line)
            html.append('<p><b>%s</b>: %s</p>' % (' '.join(speaker), ' '.join(speech)))
        elif re.match(ur'\(.*시.*분.*\)', line):
            html.append('<pre><code style="background: yellow;">%s</code></pre>' % line)
        elif re.match(ur'[0-9]+\..*', line):
            html.append('<pre><code style="background: gray;">%s</code></pre>' % line)
        else:
            html.append('<p>%s</p>' % line)
    return '\n'.join(html)

def txt2json(txt):
    d = []
    for line in filter(None, txt.split('\n')):
        if line.startswith(startsignal):
            speaker, speech = parse_speech(line)
            e = { 'type': 'statement',\
                    'content': ' '.join(speech),\
                    'person': ' '.join(speaker) }
        elif re.match(ur'\(.*시.*분.*\)', line):
            e = { 'type': 'time', 'content': line }
        elif re.match(ur'[0-9]+\..*', line):
            e = { 'type': 'issue', 'content': line }
        else:
            e = { 'type': 'unknown', 'content': line }
        d.append(e)
    return d

if __name__=='__main__':
    BASEDIR = '.'
    BASEDIR = '/home/e9t/data/popong'
    datadir = '%s/meeting-data/dialogue' % BASEDIR
    meetingdir = '%s/meetings' % BASEDIR

    filenames = utils.get_filenames(meetingdir)[:1]
    for filename in filenames:
        print filename
        filebase = filename.replace('.json', '')[2:]
        txt = utils.read_text('%s/%s.txt' % (datadir, filebase))
        html = txt2html(txt)
        with open('%s/%s.html' % (datadir, filebase), 'w') as f:
            f.write(html.encode('utf-8'))
