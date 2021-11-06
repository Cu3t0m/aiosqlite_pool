import setuptools

setuptools.setup(
    name="aiosqlite_pool",
    version="0.0.1",
    author="RouterGTX",
    author_email="alvreiusd@gmail.com",
    description="a connection pool wrapper for aiosqlite",
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=["aiosqlite"],
    license="MIT"
)