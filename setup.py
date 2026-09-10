from setuptools import setup, find_packages

setup(
    name="dwi-crawler",
    version="1.0.0",
    description="DWI Dark Web and Onion Intelligence Crawler",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dwi-crawler=dwi_crawler.cli.main:main",
        ],
    },
    install_requires=[
        "typer>=0.9.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "httpx[socks]>=0.25.0",
        "socksio>=1.0.0",
        "beautifulsoup4>=4.12.0",
        "rich>=13.7.0",
    ],
    extras_require={
        "browser": ["selenium>=4.15.0"],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
        ],
    },
)
