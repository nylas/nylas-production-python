from setuptools import setup, find_packages


setup(
    name="nylas-production-python",
    version="0.1",
    packages=find_packages(),

    install_requires=[
        "raven==5.5.0",
        "gevent==1.0.1",
        "colorlog==1.8",
        "structlog==0.4.1"],
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
