"""
Flask-RL
-------------

flask rate limiter
"""
import versioneer

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open("requirements/production.txt") as f:
    requirements = f.read().splitlines()

setup(
    name='flask_rl',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    url='http://github.com/a6enez3r/flask_rl',
    author="Abenezer Mamo",
    author_email="hi@abenezer.sh",
    license="MIT",
    description='flask rate limiter',
    long_description=long_description,
    py_modules=['flask_rl'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=requirements,
)
