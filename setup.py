import sys

from setuptools.command.test import test as TestCommand

from setuptools import setup, find_packages


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name="nylas-production-python",
    version="0.1",
    packages=find_packages(),

    install_requires=[
        "raven==5.5.0",
        "gevent>=1.0.1",
        "colorlog==1.8",
        "structlog==0.4.1"],

    tests_require=["pytest"],
    cmdclass={'test': PyTest},

    dependency_links=[],

    include_package_data=True,
    package_data={},
    data_files=[],
    scripts=[],
    zip_safe=False,
    author="Nylas Team",
    author_email="team@nylas.com",
    description="Nylas production python utilities",
    license="AGPLv3",
    keywords="nylas",
    url="https://www.nylas.com",
)
