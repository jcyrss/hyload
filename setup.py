from setuptools import find_packages, setup
from os.path import join

from hyload.cfg import Version

with open('README.md', encoding='utf8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name         = 'hyload',
    version      = Version,
    author       = 'byhy',
    author_email = 'jcyrss@gmail.com',
    url          = 'https://jcyrss.github.io/hyload',
    download_url = 'https://pypi.python.org/pypi/hyload',
    license      = 'MIT',
    description  = 'load testing library',
    long_description = LONG_DESCRIPTION,
    long_description_content_type = 'text/markdown',
    keywords     = 'hyload loadtesting',

    python_requires = '>=3.8',
    
    classifiers  = """
Development Status :: 4 - Beta
Intended Audience :: Developers
Topic :: Software Development :: Testing
License :: OSI Approved :: MIT License
""".strip().splitlines(),
  
    packages     = find_packages(
        include = ['hyload','hyload.*']
    ),
    
    package_data = {'': ['*.css','*.js']},
        
    install_requires=[   
        'gevent>=22.10.2',
        'matplotlib',
        'paramiko>=3.2.0',
        'websockets>=11.0.3',  # need byremote stats hub function
    ],
)