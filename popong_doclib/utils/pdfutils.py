#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import get
import subprocess32 as sp   # only works on POSIX machines

def pdf2xml(pdffile):
    sp.check_output(['pdftohtml', '-c', '-q', '-xml', pdffile])
    xmlfile = pdffile.replace('.pdf', '.xml')
    xmlroot = get.localtree(xmlfile)
    sp.check_call(['rm', xmlfile])
    return xmlroot
