from setuptools import setup, find_packages
from webmentiontools import __version__

setup(version=__version__,
      name="webmentiontools",
      author="Peter Molnar",
      author_email="hello@petermolnar.eu",
      description="Tools for webmention.org (forked from vrypan@gmail.com)",
      long_description=open('README.md').read(),
      packages=['webmentiontools'],
      install_requires=['beautifulsoup4', 'requests', 'docopt','arrow','bleach','emoji'],
      scripts=['bin/webmention-tools'],
      url='https://github.com/petermolnar/webmention-tools',
      license='LICENSE',
      include_package_data=True,
)
