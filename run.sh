#!/bin/bash
set -e

cd "$(dirname "$0")"
source venv/bin/activate
python -c 'import main; import backend.seed; main.initialize_application(); backend.seed.seed_produits()'
python main.py