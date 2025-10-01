from setuptools import setup, find_packages

setup(
    name='pyroxi',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A Python package for connecting to a proxy and sending packets.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/bettercallninja/pyroxi',
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
        'requests>=2.25.1',
        'aiohttp>=3.8.0',
        'httpx>=0.24.0',
        'pytest>=7.0.0',
    ],
)