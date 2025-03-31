from setuptools import setup

setup(
    name='beets-usertag',
    version='0.1',
    description='beets plugin to support user defined keyword tags',
    long_description=open('README.md').read(),
    author='Edgars Supe',
    author_email='',
    url='https://github.com/edgars-supe/beets-usertag',
    license='MIT',
    platforms='ALL',
    packages=['beetsplug'],
    install_requires=[
        'beets>=1.5.0'
    ],
    python_requires=">=3.7"
)
