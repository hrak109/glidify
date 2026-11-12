#!/bin/bash
# Start frontend preview dev server
set -e
cd "$(dirname "$0")/.."
npm install
npm run dev
