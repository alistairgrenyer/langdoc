"""
Setup configuration for langdoc package.
"""
from setuptools import setup, find_packages

setup(
    name="langdoc",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "langchain",
        "langchain_openai",
        "chromadb",
        "openai",
        "gitpython",
        "python-dotenv",
        "tenacity",
    ],
    entry_points={
        "console_scripts": [
            "langdoc=langdoc.cli:cli",
        ],
    },
    python_requires=">=3.8",
    description="A CLI tool to analyze and document Git repositories using LangChain and RAG",
    author="Alistair Grenyer",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
