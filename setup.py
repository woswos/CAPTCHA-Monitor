from setuptools import setup

setup(name='CAPTCHA Monitor',
      version='0.1',
      description='Check if a web site returns a CAPTCHA',
      url='https://github.com/woswos/CAPTCHA-Monitor',
      author='Barkin Simsek',
      author_email='barkin@nyu.edu',
      license='GPL-3.0',
      packages=['captchamonitor'],
      install_requires=[
            'selenium-wire',
            'urltools',
            'urllib3<1.25',
            'stem',
            'pysocks'
      ],
      zip_safe=False,
      entry_points={
            'console_scripts': [
            'captchamonitor = captchamonitor.__main__:main'
            ]
      })
