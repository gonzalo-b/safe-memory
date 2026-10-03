// Prepared for the existing private macserver host; not an agent supervisor.
const path = require('node:path');
const appHome = '/Users/agent/Library/Application Support/Safe Memory';
const release = process.env.MEMORY_RELEASE || path.resolve(__dirname, '..');
const python = process.env.MEMORY_PYTHON || path.join(appHome, 'runtime', 'venv', 'bin', 'python');
const common = {
  instances: 1, exec_mode: 'fork', autorestart: true, max_restarts: 5,
  min_uptime: '10s', kill_timeout: 10000, max_memory_restart: '768M',
  merge_logs: true,
};
module.exports = { apps: [
  {
    ...common, name: 'safe-memory-api', cwd: release, script: 'shell/server.py', interpreter: python,
    args: ['--root', path.join(appHome, 'alpha'), '--origin', 'https://memory.lazyagent.ai', '--trusted-edge', 'cloudflare'],
    env: { PYTHONUNBUFFERED: '1' },
    out_file: path.join(appHome, 'logs', 'api-out.log'), error_file: path.join(appHome, 'logs', 'api-error.log'),
  },
  {
    ...common, name: 'safe-memory-web', cwd: path.join(release, 'web'),
    script: path.join(release, 'web', 'node_modules', 'next', 'dist', 'bin', 'next'), interpreter: '/opt/homebrew/bin/node',
    args: ['start', '--hostname', '127.0.0.1', '--port', '8767'],
    env: { NODE_ENV: 'production', NEXT_TELEMETRY_DISABLED: '1' },
    out_file: path.join(appHome, 'logs', 'web-out.log'), error_file: path.join(appHome, 'logs', 'web-error.log'),
  },
] };
