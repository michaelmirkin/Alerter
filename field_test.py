__author__ = 'mitik'
from field import field
from consts import *
for name in field.data_dic:
    field(name)
field.load_and_compare()
