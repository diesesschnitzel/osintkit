#!/usr/bin/env node
const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const packageDir = path.dirname(path.dirname(__filename));
const isWin = process.platform === 'win32';

const venvPython = isWin
    ? path.join(packageDir, '.venv', 'Scripts', 'python.exe')
    : path.join(packageDir, '.venv', 'bin', 'python3');

// If venv doesn't exist yet, run postinstall first (self-healing first run)
if (!fs.existsSync(venvPython)) {
    const postinstall = path.join(packageDir, 'postinstall.js');
    if (fs.existsSync(postinstall)) {
        console.log('osintkit: first run — setting up Python environment...');
        const r = spawnSync(process.execPath, [postinstall], {
            stdio: 'inherit',
            cwd: packageDir,
        });
        if (!fs.existsSync(venvPython)) {
            console.error('\nosintkit: setup failed. Run manually:');
            console.error(`  node ${postinstall}`);
            process.exit(1);
        }
    }
}

function findPython() {
    // Prefer venv Python (Unix + Windows)
    const venvCandidates = [
        path.join(packageDir, '.venv', 'bin', 'python3'),
        path.join(packageDir, '.venv', 'bin', 'python'),
        path.join(packageDir, '.venv', 'Scripts', 'python.exe'),
        path.join(packageDir, 'venv', 'bin', 'python3'),
        path.join(packageDir, 'venv', 'Scripts', 'python.exe'),
    ];
    for (const p of venvCandidates) {
        if (fs.existsSync(p)) return p;
    }
    // Fall back to system Python
    const systemCandidates = isWin ? ['python', 'python3'] : ['python3.11', 'python3', 'python'];
    for (const bin of systemCandidates) {
        const r = spawnSync(bin, ['--version'], { stdio: 'pipe' });
        if (r.status === 0) return bin;
    }
    return 'python3';
}

const pythonBin = findPython();
const env = {
    ...process.env,
    PYTHONPATH: process.env.PYTHONPATH
        ? `${packageDir}${path.delimiter}${process.env.PYTHONPATH}`
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
