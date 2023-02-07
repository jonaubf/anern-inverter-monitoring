from setuptools import setup, find_packages


def _get_version():
    with open('VERSION') as fd:
        return fd.read().strip()


install_requires = [
    'aiohttp==3.8.3',
    'pyserial==3.5',
    'gunicorn==20.1.0',
]

setup(
    name='anern_monitoring',
    version=_get_version(),
    include_package_data=True,
    install_requires=install_requires,
    packages=find_packages(),
)
