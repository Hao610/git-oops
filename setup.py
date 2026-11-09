try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup
    find_packages = lambda: ["src"]

setup(
    name="git-oops",
    version="0.2.0",
    description="The Dual-Mode Terminal Crash Fixer & Autonomous AI Agent Safety Harness.",
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
