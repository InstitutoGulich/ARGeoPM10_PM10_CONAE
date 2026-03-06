from setuptools import find_packages, setup

setup(
    name="empatia",
    version="0.0.1",
    description="Support system for decision making in air quality management",
    author="CONAE-Empatia team",
    author_email="",
    classifiers=["Programming Language :: Python :: 3.8"],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "numpy",
        "pandas",
        "pyspatialml",
        "rasterio",
        "requests",
        "urllib3",
        "certifi",
        "attrs",
        "beautifulsoup4",
        "scikit-learn",
        "tqdm",
	    "harmony-py",
        "netCDF4",
        "earthaccess",
        # Note: GDAL/GRASS are provided by system packages or conda
    ],
    entry_points="""
        [console_scripts]
        empatia=empatia.cli:main
    """,
)
