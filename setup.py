from setuptools import setup, find_packages

setup(
   name='planet',
   version='1.0',
   description='Written for technical assessment',
   author='Chris Scott',
   author_email='christopher.scott925@gmail.com',
   packages=find_packages(where='src'),
   package_dir={'': 'src'},
   install_requires=[
       
        "fiona",
        "geopandas",
        "numpy",
        "openmeteo_requests",
        "pandas",
        "pyproj",
        "pyshp",
        "requests_cache",
        "retry_requests",
        "scipy",
        "Shapely",
        "SQLAlchemy",
     ],
     
     entry_points={
         'console_scripts':[
             'planet=planet_challenge.__main__:main'
         ]
     }
)