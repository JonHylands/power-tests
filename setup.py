from setuptools import setup

setup(name='powertests',
      version='1.0',
      description='Power tests for Firefox OS',
      author='Jon Hylands',
      author_email='jhylands@mozilla.com',
      url='https://github.com/JonHylands/power-tests',
      license='MPL',
      packages=['powertests'],
      install_requires=['gaiatest', 'powertool'])
