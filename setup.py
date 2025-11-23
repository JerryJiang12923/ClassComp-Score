"""
ClassComp Score 项目打包配置
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ClassComp-Score",
    version="1.1.0",
    author="ClassComp Development Team",
    description="信息委员电脑评分系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/ClassComp-Score",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "Flask>=2.0",
        "Flask-Cors>=3.0",
        "Flask-Login>=0.6.3",
        "Flask-WTF>=1.2.1",
        "WTForms>=3.1.0",
        "Werkzeug>=2.3.0",
        "pandas>=2.0",
        "pytz>=2023.3",
        "python-dotenv>=1.0",
        "psycopg2-binary>=2.9",
        "psutil>=5.9.0",
        "XlsxWriter>=3.0",
    ],
    extras_require={
        "dev": [
            "gunicorn>=21.2.0",
            "waitress>=2.1.0",
        ],
    },
)