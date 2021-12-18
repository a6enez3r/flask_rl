"""
Flask-RL
-------------

flask rate limiter
"""
from setuptools import setup

with open("requirements/prod.txt") as f:
    requirements = f.read().splitlines()

setup(
    name='flask_rl',
    version='0.0.1',
    url='http://http://github.com/abmamo/flask_rl',
    license='BSD',
    author='Abenezer Mamo',
    author_email='contact@abmamo.com',
    description='flask rate limiter',
    long_description=__doc__,
    py_modules=['flask_rl'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=requirements,
)
