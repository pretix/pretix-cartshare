import os
from setuptools import setup, find_packages


try:
    with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = ''


setup(
    name='pretix-cartshare',
    version='1.0',
    description='pretix plugin to share carts',
    long_description=long_description,
    url='https://pretix.eu',
    author='Raphael Michel',
    author_email='mail@raphaelmichel.de',

    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    entry_points="""
[pretix.plugin]
cartshare=pretix_cartshare:PretixPluginMeta
""",
)
