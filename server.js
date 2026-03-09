const fs = require("fs");
const http = require("http");
const net = require("net");
const path = require("path");

const HOST = process.env.HOST || "127.0.0.1";
const START_PORT = Number(process.env.PORT || 3000);
const STATIC_DIR = path.join(__dirname, "static");

const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon"
};

function sendFile(res, filePath) {
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not Found");
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      "Content-Type": MIME_TYPES[ext] || "application/octet-stream",
      "Cache-Control": "no-cache"
    });
    res.end(data);
  });
}

function createAppServer() {
  const server = http.createServer((req, res) => {
    const reqPath = decodeURIComponent((req.url || "/").split("?")[0]);
    const relativePath = reqPath === "/" ? "index.html" : reqPath.replace(/^\/+/, "");
    const targetPath = path.normalize(path.join(STATIC_DIR, relativePath));

    if (!targetPath.startsWith(STATIC_DIR)) {
      res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Forbidden");
      return;
    }

    fs.stat(targetPath, (err, stats) => {
      if (!err && stats.isFile()) {
        sendFile(res, targetPath);
        return;
      }

      sendFile(res, path.join(STATIC_DIR, "index.html"));
    });
  });

  server.on("error", (err) => {
    console.error(err);
    process.exit(1);
  });

  return server;
}

function checkPort(port) {
  return new Promise((resolve) => {
    const tester = net.createServer();

    tester.once("error", () => resolve(false));
    tester.once("listening", () => {
      tester.close(() => resolve(true));
    });

    tester.listen(port, HOST);
  });
}

async function findAvailablePort(startPort) {
  let port = startPort;
  while (!(await checkPort(port))) {
    port += 1;
  }
  return port;
}

(async () => {
  const port = await findAvailablePort(START_PORT);
  const server = createAppServer();

  server.listen(port, HOST, () => {
    console.log(`Heart Mirror frontend running at http://${HOST}:${port}`);
    console.log("FastAPI backend should run at http://localhost:8000");
    if (port !== START_PORT) {
      console.log(`Port ${START_PORT} was busy, switched to ${port}.`);
    }
  });
})();
