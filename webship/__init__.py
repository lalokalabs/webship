import os
import configparser

from invoke import Collection, Program
from invoke.util import yaml
from webship import tasks

config = configparser.ConfigParser()
try:
    config.read("webship.ini")
except Exception as e:
    print(e)
    config = {"fetch": {}, "build": {}, "deploy": {}}

print(config)
ns = Collection.from_module(tasks)
ns.configure({"webship": {s:dict(config.items(s)) for s in config.sections()}})
program = Program(namespace=ns, version='0.1.0')
