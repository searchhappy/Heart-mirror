const backendPort = window.__BACKEND_PORT__ || "8000";
const backendHost = window.location.hostname || "localhost";
const sameBackendOrigin = window.location.port === backendPort;

window.__API_BASE__ = sameBackendOrigin
  ? window.location.origin
  : `${window.location.protocol}//${backendHost}:${backendPort}`;
