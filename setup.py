from setuptools import setup, find_packages

setup(
    name="blog-builder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "markdown>=3.4.0",
    ],
    entry_points={
        "console_scripts": [
            "build-blog=blog.build:main",
        ],
    },
    python_requires=">=3.8",
) 