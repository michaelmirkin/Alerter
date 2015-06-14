__author__ = 'mitik'
from field import field
from consts import *
for name in LISTOBJECTS:
    field(name)
field.load_and_compare()
