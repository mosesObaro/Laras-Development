from setuptools import setup, find_packages

setup(
    name="preuni-system",
    version="1.0.0",
    description="18-Month Pre-University Development, Career & Opportunity System (UNIBEN Healthcare Track)",
    author="Antigravity Development Team",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "preuni=preuni_system.cli:main",
        ],
    },
)
