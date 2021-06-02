"""
SQLAlchemy-Searchable
---------------------

Provides fulltext search capabilities for declarative SQLAlchemy models.
"""

import os
import re

from setuptools import setup

HERE = os.path.dirname(os.path.abspath(__file__))


def get_version():
    filename = os.path.join(HERE, 'sqlalchemy_searchable', '__init__.py')
    with open(filename) as f:
        contents = f.read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


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
    python_requires='>=3.6',
    install_requires=[
        'SQLAlchemy>=1.3.0',
        'SQLAlchemy-Utils>=0.37.5',
        'validators>=0.3.0',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
