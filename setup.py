from setuptools import setup, find_packages

setup(
    name="agent2",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers",  
        "tree-sitter==0.21.3",
        "tree-sitter-languages"
    ],
)