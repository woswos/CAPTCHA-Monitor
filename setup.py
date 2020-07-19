from setuptools import setup

with open('requirements.txt') as f:
    install_requires = f.readlines()

setup(name='CAPTCHA Monitor',
      version='0.2.0',
      description='Check if a web site returns a CAPTCHA',
      url='https://github.com/woswos/CAPTCHA-Monitor',
      author='Barkin Simsek',
      author_email='barkin@nyu.edu',
      license='GPL-3.0',
      packages=['captchamonitor'],
      install_requires=install_requires,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'captchamonitor = captchamonitor.captchamonitor:main'
          ]
      })
