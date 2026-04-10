#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// The npm package root is one level up from bin/
const packageDir = path.dirname(path.dirname(__filename));

// Prefer venv Python (installed by postinstall), fall back to system Python
function findPython() {
    const venvCandidates = [
        path.join(packageDir, '.venv', 'bin', 'python3'),
        path.join(packageDir, '.venv', 'bin', 'python'),
        path.join(packageDir, 'venv', 'bin', 'python3'),
        path.join(packageDir, 'venv', 'bin', 'python'),
    ];
    for (const p of venvCandidates) {
        if (fs.existsSync(p)) return p;
    }

    // Fall back to system Python
    const systemCandidates = ['python3.11', 'python3', 'python'];
    for (const bin of systemCandidates) {
        try {
            require('child_process').execSync(`${bin} --version`, { stdio: 'ignore' });
            return bin;
        } catch (_) {}
    }
    return 'python3';
}

const pythonBin = findPython();

// Always set PYTHONPATH so the package is importable regardless of install method
const env = {
    ...process.env,
    PYTHONPATH: process.env.PYTHONPATH
        ? `${packageDir}:${process.env.PYTHONPATH}`
        : packageDir,
};

const child = spawn(pythonBin, ['-m', 'osintkit', ...process.argv.slice(2)], {
    stdio: 'inherit',
    cwd: packageDir,
    env,
});

child.on('error', () => {
    console.error('Error: Python 3.10+ required. Install from https://python.org');
    process.exit(1);
});

child.on('close', (code) => process.exit(code || 0));
