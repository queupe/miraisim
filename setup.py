from distutils.core import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='miraisim',
    description='Botnet propagation simulator',
    long_description=long_description,
    version='0.0.1',
    author='Italo Cunha',
    author_email='cunha@dcc.ufmg.br',
    # url='https://github.com/PEERINGTestbed/powerdns-pdyndns-backend',
    scripts=['miraisim.py'],
    # packages=['ripe', 'ripe.atlas', 'ripe.atlas.dyndns'],
    license='GPLv3',
    classifiers=[
        # 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.3',
        'Operating System :: POSIX',
        # 'Topic :: System :: Networking',
        'Development Status :: 3 - Alpha'
    ]
)
