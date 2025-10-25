from setuptools import setup

with open('hyload/product.py') as f:
    productInfo = f.read()

import re
Version = re.findall(r'version\s*=\s*[\'"](.+?)[\'"]', productInfo)[0]
print(f'$$$$ Version: {Version}')

setup(
    version      = Version,
)