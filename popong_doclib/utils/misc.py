#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import json
import os


def check_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def chunk(items, idx, i):
    # i: start index
    try:
        return items[idx[i]:idx[i+1]]
    except IndexError:
        return items[idx[i]:]

def chunk_all(items, idx):
    return [chunk(items, idx, i) for i in range(len(idx))]

def get_filenames(basedir):
    os.chdir(basedir)
    return [os.path.join(path, name).decode('utf-8')\
            for path, subdirs, files in os.walk('.')\
                for name in files]

def get_textelems(xmlroot):
    textelems = []
    pages = xmlroot.xpath('//page')
    for i, page in enumerate(pages):
        elems = page.xpath('.//text')
        if not i==0:
            elems = elems[1:]
        textelems.extend(elems)
    return textelems

def read_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def read_text(filename, encoding='utf-8'):
    with open(filename, 'r') as f:
        return f.read().decode(encoding).split('\n')

def write_json(data, filename, checkdir=True):
    if checkdir:
        check_dir(os.path.dirname(filename))
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def write_text(text, filename, checkdir=True):
    if checkdir:
        check_dir(os.path.dirname(filename))
    with open(filename, 'w') as f:
        f.write(text.encode('utf-8'))
