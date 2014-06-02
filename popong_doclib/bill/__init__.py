#! /usr/bin/python2.7

from ..base import polymorph
import national

def parse(source, region='national'):
    signature = (region,)
    impl =  parse.dict[signature]
    return impl(source)

@polymorph(parse, 'national')
def parse_national_bills(text):
    national.parse(text)
