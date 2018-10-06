from setuptools import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='weekly-calendar',
    version='0.1.0',
    author='kardaj',
    author_email='bensalemhsn@gmail.com',
    description='A simple library to deal with weekly opening hours and other recurrent weekly events',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/kardaj/weekly-calendar',
    install_requires=['pytz', 'tzlocal'],
    packages=['weekly_calendar'],
    classifiers=(
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ),

)
