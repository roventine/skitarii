import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="skitarii",
    version="0.0.4",
    author="roventine",
    author_email="ukyotachibana@yeah.net",
    description="automata for routine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/roventine/skitarii",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['requests', 'lxml', 'logbook', 'demjson'],
)
