from setuptools import setup, find_packages

with open('README.md') as file:
    long_description = file.read()

setup(
    name='alpino-query',
    python_requires='>=3.7, <4',
    version='2.1.12',
    description='Generating XPATH queries based on a Dutch Alpino syntax tree and user-specified token properties.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Digital Humanities Lab, Utrecht University',
    author_email='digitalhumanities@uu.nl',
    url='https://github.com/CentreForDigitalHumanities/alpino-query',
    license='CC BY-NC-SA 4.0',
    packages=['alpino_query'],
    package_data={"alpino_query": ["py.typed"]},
    zip_safe=True,
    install_requires=[
        'requests',
        'lxml'
    ],
    entry_points={
        'console_scripts': [
            'alpino-query = alpino_query.__main__:main'
        ]
    })
