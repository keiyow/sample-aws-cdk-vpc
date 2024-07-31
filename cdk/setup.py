import setuptools

cdk_version = "2.150.0"
setuptools.setup(
    name="cdk",
    version="0.0.1",
    description="An empty CDK Python app",
    author="author",
    package_dir={"": "cdk"},
    packages=setuptools.find_packages(where="cdk", exclude=("tests",)),
    install_requires=[
        "aws-cdk-lib=={}".format(cdk_version),
        "constructs>=10.1.42",
        "mypy>=0.910",
        "pyyaml>=5.4.1",
        "pytest==7.4.3",
        "syrupy==4.6.0",
        "moto==4.2.12",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    extras_require={"test": ["pytest", "syrupy"]},
)
