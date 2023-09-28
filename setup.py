from setuptools import setup #,find_packages
# from package import Package

setup(
    author="Sean Crowley",
    author_email="sean.crowley@datirium.com",
    # packages=find_packages(),
    # include_package_data=True,
    # cmdclass={
    #     "package": Package
    # },
    name="sat-cluster-api",
    version="0.1.1",
    description="API for starting sample runs with cwl-toil.",
    py_modules=["sat_cluster_api"],
    entry_points={
        "console_scripts": ["start-cluster-api=__main__:run_app"],
    },
)