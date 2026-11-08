from setuptools import setup, find_packages

setup(
    name="git-oops",
    version="0.1.0",
    description="Brutally honest terminal crash fixer with daily spend-protection circuit breaker.",
    author="Hao",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pytest>=7.0.0"
    ],
    entry_points={
        "console_scripts": [
            "git-oops = src.cli:main",
        ],
    },
    python_requires=">=3.9",
)
