from setuptools import setup, find_packages

setup(
    name="marketflow",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "yfinance>=0.2.31",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "pytz>=2023.3",
        "python-dateutil>=2.8.2",
        "exchange-calendars>=4.5.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0"
    ],
    author="chinnsenn",
    description="A market trend following trading system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
)
