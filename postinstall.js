#!/usr/bin/env node
/**
 * osintkit postinstall — creates a venv inside the package dir and installs
 * all Python dependencies into it. The npm shim (bin/osintkit.js) will then
 * always find and use this venv's Python, avoiding any system Python confusion.
 */

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const packageDir = __dirname;
const venvDir = path.join(packageDir, '.venv');
const req = path.join(packageDir, 'requirements.txt');
const reqTools = path.join(packageDir, 'requirements-tools.txt');

// Platform-aware paths inside the venv
const isWin = process.platform === 'win32';
const venvPython = isWin
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python3');
const venvPip = isWin
    ? path.join(venvDir, 'Scripts', 'pip.exe')
    : path.join(venvDir, 'bin', 'pip3');

function findSystemPython() {
    const candidates = isWin
        ? ['python', 'python3']
        : ['python3.13', 'python3.12', 'python3.11', 'python3.10', 'python3'];
    for (const bin of candidates) {
        const r = spawnSync(bin, ['--version'], { encoding: 'utf8' });
        if (r.status === 0) {
            // Must be >= 3.10
            const match = (r.stdout || r.stderr || '').match(/Python (\d+)\.(\d+)/);
            if (match && (parseInt(match[1]) > 3 || parseInt(match[2]) >= 10)) {
                return bin;
            }
        }
    }
    return null;
}

function run(cmd, args, opts = {}) {
    const r = spawnSync(cmd, args, { encoding: 'utf8', cwd: packageDir, ...opts });
    return r;
}

console.log('\nosintkit: setting up Python environment...\n');

// Step 1: find a usable Python 3.10+
const sysPython = findSystemPython();
if (!sysPython) {
    console.log('  ❌  Python 3.10+ not found.');
    console.log('      Install from https://python.org then re-run: npm install -g osintkit\n');
    process.exit(0);
}
console.log(`  ✅  Found Python: ${sysPython}`);

// Step 2: create venv (skip if already exists)
if (!fs.existsSync(venvPython)) {
    console.log(`  🔧  Creating venv at ${venvDir} ...`);
    const r = run(sysPython, ['-m', 'venv', venvDir]);
    if (r.status !== 0) {
        console.log('  ❌  Failed to create venv.');
        console.log(`      ${(r.stderr || '').trim()}`);
        console.log('      Try: python3 -m venv .venv (in the package dir)\n');
        process.exit(0);
    }
    console.log('  ✅  Venv created');
} else {
    console.log('  ✅  Venv already exists');
}

// Step 3: upgrade pip inside venv
run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip', '-q']);

// Step 4: install deps into venv
function pipInstall(requirementsFile, label) {
    if (!fs.existsSync(requirementsFile)) return;
    console.log(`  📦  Installing ${label}...`);
    const r = run(venvPython, ['-m', 'pip', 'install', '-r', requirementsFile, '-q', '--disable-pip-version-check']);
    if (r.status === 0) {
        console.log(`  ✅  ${label} installed`);
    } else {
        const err = (r.stderr || r.stdout || '').trim().split('\n').slice(-3).join('\n');
        console.log(`  ❌  ${label} failed:\n      ${err}`);
        console.log(`      Fix: ${venvPython} -m pip install -r ${requirementsFile}`);
    }
}

pipInstall(req, 'Core dependencies (typer, rich, httpx...)');
pipInstall(reqTools, 'OSINT tools (maigret, holehe, sherlock)');

console.log('\n  ✅  osintkit ready. Run: osintkit new\n');
