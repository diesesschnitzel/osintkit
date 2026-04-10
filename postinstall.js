#!/usr/bin/env node
/**
 * osintkit postinstall — installs all Python dependencies automatically.
 *
 * Runs after `npm install -g osintkit`.
 * Installs:
 *   1. Core Python deps (typer, rich, httpx, pydantic, etc.) from requirements.txt
 *   2. Optional OSINT tools (maigret, holehe, sherlock) from requirements-tools.txt
 *
 * Uses --break-system-packages on Linux/macOS where needed (Python 3.11+).
 * Falls back gracefully if pip isn't available.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const packageDir = __dirname;
const req = path.join(packageDir, 'requirements.txt');
const reqTools = path.join(packageDir, 'requirements-tools.txt');

function findPip() {
    for (const bin of ['pip3', 'pip']) {
        try {
            execSync(`${bin} --version`, { stdio: 'ignore' });
            return bin;
        } catch (_) {}
    }
    return null;
}

function pipInstall(pip, requirementsFile, label) {
    if (!fs.existsSync(requirementsFile)) {
        console.log(`  ⚠️  ${label}: requirements file not found, skipping`);
        return;
    }

    const flags = ['-r', requirementsFile, '-q', '--disable-pip-version-check'];

    // Try with --break-system-packages first (needed on modern Linux/macOS)
    try {
        execSync(`${pip} install ${flags.join(' ')} --break-system-packages`, {
            stdio: 'pipe',
            cwd: packageDir,
        });
        console.log(`  ✅  ${label} installed`);
        return;
    } catch (_) {}

    // Fall back without the flag (works on older systems / virtual envs)
    try {
        execSync(`${pip} install ${flags.join(' ')}`, {
            stdio: 'pipe',
            cwd: packageDir,
        });
        console.log(`  ✅  ${label} installed`);
        return;
    } catch (err) {
        console.log(`  ⚠️  ${label}: could not install (${err.message.split('\n')[0]})`);
    }
}

console.log('\nosintkit: installing Python dependencies...\n');

const pip = findPip();
if (!pip) {
    console.log('  ⚠️  pip not found — skipping Python dependency install.');
    console.log('  Run manually: pip3 install -r requirements.txt -r requirements-tools.txt');
    process.exit(0);
}

pipInstall(pip, req, 'Core dependencies');
pipInstall(pip, reqTools, 'OSINT tools (maigret, holehe, sherlock)');

console.log('\nosintkit ready. Run: osintkit new\n');
