name: Visualize Performance

on:
  workflow_dispatch:

jobs:
  visualize:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas matplotlib

      - name: Ensure performance is a package
        run: |
          touch backtesting/__init__.py

      - name: Run performance visualizer
        run: |
          echo "Running performance visualizer..."
          export PYTHONPATH="${{ github.workspace }}"
          python backtesting/performance_visualizer.py
