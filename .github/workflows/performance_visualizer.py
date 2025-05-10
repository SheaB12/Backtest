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

      - name: Ensure package structure
        run: |
          touch backtesting/__init__.py

      - name: Run performance visualizer
        run: |
          echo "Running performance visualizer..."
          export PYTHONPATH="${{ github.workspace }}"
          python backtesting/performance_visualizer.py

      - name: Zip performance plots
        run: |
          cd backtesting/performance_charts
          zip -r performance_plots.zip *.png

      - name: Upload zipped plots as artifact
        uses: actions/upload-artifact@v3
        with:
          name: performance-plots
          path: backtesting/performance_charts/performance_plots.zip
