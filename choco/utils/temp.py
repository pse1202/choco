#-*- coding: utf-8 -*-
import os
from choco import home
from .generator import random_str

def generate_temp_name():
    tmp_dir = os.path.join(home, 'tmp')
    name = os.path.join(tmp_dir, random_str(12))

    while os.path.isfile(name):
        name = os.path.join(tmp_dir, random_str(12))

    return name

def get_temp_dir():
    return os.path.join(home, 'tmp')

def clear_temp_dir():
    pass
