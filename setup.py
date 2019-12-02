from setuptools import setup
import pip

setup(
    name='site-monitoring',
    version='1.0',
    packages=[''],
    url='',
    license='',
    author='Anass Elidrissi',
    author_email='anasselidrissi97@gmail.com',
    description='take home project for datadog', install_requires=['requests', 'tzlocal', 'flask']
)

py_modules = ['site_monitor', 'main', 'user_interface', 'utils']

if __name__ == '__main__':

    from sys import platform
    if platform == 'windows':
        pip.main(['install', 'windows-curses'])
