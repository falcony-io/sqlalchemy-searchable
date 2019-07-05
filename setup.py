"""
SQLAlchemy-Searchable
---------------------

Provides fulltext search capabilities for declarative SQLAlchemy models.
"""

import os
import re
from setuptools import setup

try:
    import __pypy__
except ImportError:
    __pypy__ = None


HERE = os.path.dirname(os.path.abspath(__file__))


def get_version():
    filename = os.path.join(HERE, 'sqlalchemy_searchable', '__init__.py')
    with open(filename) as f:
        contents = f.read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


extras_require = {
    'test': [
        'pytest>=2.2.3',
        'psycopg2cffi>=2.6.1' if __pypy__ else 'psycopg2>=2.4.6',
        'flake8>=2.4.0',
        'isort>=3.9.6'
    ],
}

setup(
    name='SQLAlchemy-Searchable',
    version=get_version(),
    url='https://github.com/kvesteri/sqlalchemy-searchable',
    license='BSD',
    author='Konsta Vesterinen',
    author_email='konsta@fastmonkeys.com',
    description=(
        'Provides fulltext search capabilities for declarative SQLAlchemy'
        ' models.'
    ),
    long_description=__doc__,
    packages=['sqlalchemy_searchable'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'SQLAlchemy>=0.9.0',
        'SQLAlchemy-Utils>=0.29.0',
        'validators>=0.3.0',
    ],
    extras_require=extras_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
