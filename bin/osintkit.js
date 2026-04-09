#!/usr/bin/env node
const { spawn } = require('child_process');
const python = spawn('python3', ['-m', 'osintkit', ...process.argv.slice(2)], {
    stdio: 'inherit', env: process.env
});
python.on('error', () => { console.error('Python 3.10+ required'); process.exit(1); });
python.on('close', (code) => process.exit(code || 0));
