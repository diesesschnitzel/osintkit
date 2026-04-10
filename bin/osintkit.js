#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Prefer python3.11, fall back to python3, then python
function findPython() {
    const candidates = ['python3.11', 'python3', 'python'];
    for (const bin of candidates) {
        try {
            require('child_process').execSync(`${bin} --version`, { stdio: 'ignore' });
            return bin;
        } catch (_) {}
    }
    return 'python3';
}

const python = spawn(findPython(), ['-m', 'osintkit', ...process.argv.slice(2)], {
    stdio: 'inherit',
    env: process.env
});

python.on('error', () => {
    console.error('Error: Python 3.10+ required. Install from https://python.org');
    process.exit(1);
});

python.on('close', (code) => process.exit(code || 0));
