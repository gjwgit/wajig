"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils.

from setuptools import setup, find_packages

# To use a consistent encoding:

from codecs import open

from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.

with open(path.join(here, 'docs/README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='wajig',
    version='3.2.7',  # DO NOT MODIFY. Managed from Makefile.
    description='Ubunut admin managemetn tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Graham Williams',
    author_email='wajig@togaware.com',
    url='https://wajig.togaware.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ],
    keywords='debian ubuntu admin',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    package_data={
        '.': ['LICENSE'],
        'wajig': [
            'bash_completion.d/wajig.bash'],
    },
    entry_points={'console_scripts': ['wajig=wajig:main']},
    install_requires=[
        'distro',
        'fuzzywuzzy',
        'python-Levenshtein',
    ],
    include_package_data=True,
)

# How to effect this:
#
# cp ~/.local/lib/python3.8/site-packages/wajig/bash_completion.d/wajig.bash ~/.local/share/bash-completion/completions/wajig
#
# Maybe something like the following assuming this is run from lib/python3.8/site-packages
#
# cp wajig/bash_completion.d/wajig.bash ../../../share/bash-completion/completions/wajig
# 
# os.system("cp wajig/bash_completion.d/wajig.bash ../../../share/bash-completion/completions/wajig")
#
# Need to make sure directory path exists.
