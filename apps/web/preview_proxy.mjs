const PREVIEW_PROXY_PATHS = [
  "/api/v1/snapshot",
  "/api/v1/topic-intelligence",
  "/api/v2",
];

const FORWARDED_HEADER_BLOCKLIST = [
  "authorization",
  "cookie",
  "proxy-authorization",
  "x-api-key",
  "x-api-token",
  "x-forwarded-authorization",
];

function isLoopbackHostname(hostname) {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
}

export function normalizeReadOnlyApiOrigin(value) {
  if (!value) return "";

  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("PREVIEW_READ_API_ORIGIN_INVALID");
  }

  if (parsed.username || parsed.password || parsed.pathname !== "/" || parsed.search || parsed.hash) {
    throw new Error("PREVIEW_READ_API_ORIGIN_MUST_BE_ORIGIN_ONLY");
  }

  if (parsed.protocol === "https:") return parsed.origin;
  if (parsed.protocol === "http:" && isLoopbackHostname(parsed.hostname)) return parsed.origin;
  throw new Error("PREVIEW_READ_API_ORIGIN_MUST_BE_HTTPS_OR_LOCAL_LOOPBACK");
}

export function isReadOnlyPreviewMethod(method) {
  return method === "GET" || method === "HEAD";
}

export function isAllowedPreviewProxyPath(pathname) {
  return PREVIEW_PROXY_PATHS.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

function stripSensitiveHeaders(proxyReq) {
  for (const header of FORWARDED_HEADER_BLOCKLIST) proxyReq.removeHeader(header);
}

function previewProxyGuard(req, res, next) {
  const pathname = new URL(req.url ?? "/", "http://localhost").pathname;
  if (!pathname.startsWith("/api/")) return next();

  if (!isAllowedPreviewProxyPath(pathname)) {
    res.statusCode = 404;
    res.end("Not found");
    return undefined;
  }

  if (!isReadOnlyPreviewMethod(req.method ?? "GET")) {
    res.statusCode = 405;
    res.setHeader("Allow", "GET, HEAD");
    res.end("Read-only Preview proxy");
    return undefined;
  }

  return next();
}

export function createReadOnlyPreviewProxy(value) {
  const target = normalizeReadOnlyApiOrigin(value);
  if (!target) return { target: "", proxy: {}, plugin: null };

  const proxy = Object.fromEntries(
    PREVIEW_PROXY_PATHS.map((pathname) => [pathname, {
      target,
      changeOrigin: true,
      secure: target.startsWith("https://"),
      configure(proxyServer) {
        proxyServer.on("proxyReq", stripSensitiveHeaders);
      },
    }]),
  );

  return {
    target,
    proxy,
    plugin: {
      name: "topicpilot-preview-read-only-proxy-guard",
      configureServer(server) {
        server.middlewares.use(previewProxyGuard);
      },
    },
  };
}

