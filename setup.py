import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="google_patent_scraper_add",
    version="1.0.8",
    author="xiaoximu",
    description="A package to scrape patents from 'https://patents.google.com/'",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xiaoximu/google_patent_scraper_add_master",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
    "beautifulsoup4>=4.9",
    ]
)
