#!/bin/bash

# Script to run backend tests

echo "Installing test dependencies..."
pip install -r requirements-test.txt

echo ""
echo "Running tests..."
pytest -v

echo ""
echo "Generating coverage report..."
pytest --cov=app --cov-report=html --cov-report=term

echo ""
echo "Tests completed! Coverage report available at htmlcov/index.html"
