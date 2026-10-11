// PM2 process config - matches the pattern already used for AML-Portal on this VPS.
// One-time setup: pm2 start ecosystem.config.js
// After that: pm2 restart ai-calling-bot (deploy.sh does this for you)
module.exports = {
  apps: [
    {
      name: "ai-calling-bot",
      script: "app/main.py",
      // Pipecat's dev runner binds to localhost by default - needs this to be
      // reachable from outside the VPS at all (confirmed via `ss -tlnp`).
      // A local coturn TURN server on 443 was tried to route around the VPS
      // firewall blocking direct UDP, but its auth kept failing (401) even
      // after the recommended turnadmin fix, and it required stopping
      // AML-Portal's nginx (which also needs 443) - abandoned. Real fix is
      // opening WebRTC's ports in Hostinger's firewall panel directly - see
      // docs/03_DECISIONS_LOG.md.
      args: ["--host", "0.0.0.0"],
      interpreter: "./venv/bin/python3",
      cwd: __dirname,
      env: {
        PYTHONUNBUFFERED: "1", // without this, Python buffers stdout and logs show up late/out of order under PM2
      },
      out_file: "./logs/out.log",
      error_file: "./logs/error.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      min_uptime: "15s", // crash-loop guard: a restart counts toward max_restarts only if it dies before this
    },
  ],
};
