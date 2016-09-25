from setuptools import setup, find_packages


setup(
    name='pretix-cartshare',
    version='1.0',
    description='pretix cartshare',
    long_description='pretix cartshare',
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
