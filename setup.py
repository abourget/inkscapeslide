try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='InkscapeSlide',
    version="1.0",
    description='Inkscape Slide - the Inkscape Presentation maker',
    author='Alexandre Bourget',
    author_email='alex@bourget.cc',
    url='http://projects.abourget.net',
    license='GPLv3',
    install_requires=["pyPdf",
                      ],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'inkscapeslide': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors = {'inkscapeslide': [
    #        ('**.py', 'python', None)]},
    entry_points="""
    [console_scripts]
    inkscapeslide = inkscapeslide:main

    """,
)


