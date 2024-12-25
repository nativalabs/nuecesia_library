from setuptools import setup, find_packages

setup(
    name="nuecesia_library",
    version="0.1.2",
    packages=find_packages(include=['dashboard_package', 'cloud_function_package']),
    install_requires=[],  # Add dependencies here if needed
    author="Gabriel Nativa",
    description="Centralized functions for NuecesIA.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url = "https://github.com/nativalabs/nuecesia-library", 
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
