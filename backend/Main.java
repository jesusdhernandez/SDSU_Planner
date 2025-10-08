import com.sun.net.httpserver.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.file.*;
import java.util.*;

public class Main {

    public static void main(String[] args) throws IOException {
        int port = 8080;

        // Point this to your frontend folder
        Path rootDir = Paths.get("..", "frontend").toAbsolutePath().normalize();
        if (!Files.isDirectory(rootDir)) {
            System.err.println("Frontend folder not found at: " + rootDir);
            System.err.println("Edit rootDir path in Main.java if your structure is different.");
            System.exit(1);
        }

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        // 1) API: /api/health
        server.createContext("/api/health", exchange -> {
            try {
                if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                    sendText(exchange, 405, "Method Not Allowed");
                    return;
                }
                byte[] body = "{\"status\":\"OK\"}".getBytes();
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, body.length);
                try (OutputStream os = exchange.getResponseBody()) { os.write(body); }
            } finally { exchange.close(); }
        });

        // 2) Static files (everything else)
        server.createContext("/", exchange -> {
            try {
                if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                    sendText(exchange, 405, "Method Not Allowed");
                    return;
                }
                // Resolve path safely (avoid ../ traversal)
                URI uri = exchange.getRequestURI();
                String rawPath = uri.getPath();

                // Default to index.html
                if (rawPath.equals("/")) rawPath = "/index.html";

                Path requested = rootDir.resolve("." + rawPath).normalize();

                // Block path traversal outside root
                if (!requested.startsWith(rootDir) || !Files.exists(requested) || Files.isDirectory(requested)) {
                    sendText(exchange, 404, "Not Found");
                    return;
                }

                String contentType = guessContentType(requested);
                byte[] data = Files.readAllBytes(requested);

                exchange.getResponseHeaders().set("Content-Type", contentType);
                exchange.sendResponseHeaders(200, data.length);
                try (OutputStream os = exchange.getResponseBody()) { os.write(data); }
            } catch (IOException e) {
                e.printStackTrace();
                sendText(exchange, 500, "Server Error");
            } finally { exchange.close(); }
        });

        server.setExecutor(null);
        System.out.println("Server on http://localhost:" + port);
        System.out.println("Serving frontend from: " + rootDir);
        server.start();
    }

    private static void sendText(HttpExchange ex, int status, String text) throws IOException {
        byte[] bytes = text.getBytes();
        ex.getResponseHeaders().set("Content-Type", "text/plain; charset=utf-8");
        ex.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(bytes); }
    }

    private static String guessContentType(Path p) {
        String name = p.getFileName().toString().toLowerCase(Locale.ROOT);
        if (name.endsWith(".html") || name.endsWith(".htm")) return "text/html; charset=utf-8";
        if (name.endsWith(".css")) return "text/css; charset=utf-8";
        if (name.endsWith(".js")) return "application/javascript; charset=utf-8";
        if (name.endsWith(".json")) return "application/json; charset=utf-8";
        if (name.endsWith(".png")) return "image/png";
        if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "image/jpeg";
        if (name.endsWith(".svg")) return "image/svg+xml";
        if (name.endsWith(".ico")) return "image/x-icon";
        return "application/octet-stream";
    }
}
