__author__ = 'mitik'
from field import Field

for name in Field.data_dic:
    Field(name)
Field.load_and_compare()
