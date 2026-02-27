"""Setup script for IBIS (Integrated Brain Information System) — optional pip install -e ."""

from setuptools import setup, find_packages

def read(f):
    with open(f, "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="ibis",
    version="1.0.0",
    author="NeuroPathPredict Team",
    description="Integrated Brain Information System — neuroimaging pipeline for covariate extraction",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/neuropathpredict/IBIS",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "nibabel>=3.2.0",
        "nilearn>=0.9.0",
        "scikit-learn>=1.0.0",
        "scipy>=1.7.0",
        "joblib>=1.1.0",
        "PyYAML>=6.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "tqdm>=4.62.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    keywords="neuroimaging MRI ROI buffer-zone covariate extraction",
)
