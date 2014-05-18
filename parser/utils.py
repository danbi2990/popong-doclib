#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import json
import os

def get_filenames(basedir):
    os.chdir(basedir)
    return [os.path.join(path, name).decode('utf-8')\
            for path, subdirs, files in os.walk('.')\
                for name in files]

def chunk(items, idx, i):
    # i: start index
    try:
        return items[idx[i]:idx[i+1]]
    except IndexError:
        return items[idx[i]:]

def chunk_all(items, idx):
    return [chunk(items, idx, i) for i in range(len(idx))]

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
