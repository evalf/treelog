from setuptools import setup
import os, re

with open(os.path.join('treelog', '__init__.py')) as f:
  version = next(filter(None, map(re.compile("^version = '([a-zA-Z0-9.]+)'$").match, f))).group(1)

if os.getenv('TREELOG_USE_MYPYC', None) == '1':
  from mypyc.build import mypycify
  import pathlib
  ext_modules = mypycify([str(p) for p in pathlib.Path('treelog').glob('*.py') if p.name not in {'__init__.py', 'proto.py'}])
else:
  ext_modules = []

utils = 'fetch', 'animate', 'gc'

setup(
  name = 'treelog',
  version = version,
  description = 'Logging framework that organizes messages in a tree structure',
  author = 'Evalf',
  author_email = 'info@evalf.com',
  url = 'https://github.com/evalf/treelog',
  packages = ['treelog'],
  package_data = {'treelog': ['py.typed']},
  ext_modules=ext_modules,
  entry_points = {'console_scripts': ['treelog-{0}=treelog._util:{0}'.format(util) for util in utils]},
  license = 'MIT',
  python_requires = '>=3.5',
  install_requires = ['typing_extensions'],
  extras_require = dict(docs=['Sphinx>=1.6']),
)
