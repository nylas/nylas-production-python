import sys
import os

from setuptools.command.test import test as TestCommand

from setuptools import setup, find_packages

from nylas._production_python_version import __VERSION__


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['tests']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'publish':
            os.system('git push --follow-tags && python setup.py sdist upload')
            sys.exit()
        elif sys.argv[1] == 'release':
            if len(sys.argv) < 3:
                type_ = 'patch'
            else:
                type_ = sys.argv[2]
            os.system('bumpversion --current-version {} {}'
                      .format(__VERSION__, type_))
            sys.exit()

    setup(
        name="nylas-production-python",
        version=__VERSION__,
        packages=find_packages(),

        install_requires=[
            "raven>=5.5.0",
            "gevent>=1.0.1",
            "colorlog>=1.8",
            "structlog>=16.1.0",
            "gunicorn>=19.0.0",
        ],

        tests_require=["pytest", "coverage"],
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
        keywords="nylas api production",
        url="https://www.nylas.com",
    )


if __name__ == '__main__':
    sys.exit(main())
