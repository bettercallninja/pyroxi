from setuptools import setup, find_packages

setup(
    name='pyroxy',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A Python package for connecting to a proxy and sending packets.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/pyroxy',
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Networking",
    ],
    python_requires='>=3.6',
    install_requires=[
        # List your package dependencies here
    ],
)