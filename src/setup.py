from setuptools import setup

__version__ = None
# pylint: disable=W0122,R1732
exec(open("captchamonitor/version.py").read())

setup(
    name="CAPTCHA Monitor",
    version=__version__,
    description="Check if a web site returns a CAPTCHA",
    url="https://gitlab.torproject.org/woswos/CAPTCHA-Monitor",
    author="Barkin Simsek",
    author_email="barkin@nyu.edu",
    license="GPL-3.0",
    packages=["captchamonitor"],
)
