package com.r2i.cashflow.fingermatcher;

import com.r2i.cashflow.fingermatcher.endpoints.ExtractEndpoint;
import com.r2i.cashflow.fingermatcher.endpoints.MatchEndpoint;
import com.r2i.cashflow.fingermatcher.endpoints.HealthEndpoint;
import io.javalin.Javalin;

import java.util.Map;

/**
 * Entrypoint del microservicio FingerMatcher.
 * Expone tres endpoints HTTP en el puerto configurado (default 8080):
 *   POST /extract  - extrae template de imagen
 *   POST /match    - compara dos templates y devuelve score
 *   GET  /health   - healthcheck
 *
 * No autentica requests. Confia en aislamiento de red Docker (no expuesto
 * fuera del network interno).
 */
public class FingerMatcherApp {

    public static final String VERSION = "1.0.0";
    public static final String ENGINE = "sourceafis-3.18.1";
    public static final long STARTUP_TIME_MS = System.currentTimeMillis();

    public static void main(String[] args) {
        int port = Integer.parseInt(System.getenv().getOrDefault("HTTP_PORT", "8080"));

        Javalin app = Javalin.create(config -> {
            config.requestLogger.http((ctx, executionTimeMs) -> {
                System.out.printf("%s %s -> %d (%.1fms)%n",
                    ctx.method(), ctx.path(), ctx.status().getCode(), executionTimeMs);
            });
        });

        app.post("/extract", ExtractEndpoint::handle);
        app.post("/match", MatchEndpoint::handle);
        app.get("/health", HealthEndpoint::handle);

        // Manejo uniforme de errores
        app.exception(IllegalArgumentException.class, (e, ctx) -> {
            ctx.status(400).json(Map.of("error", e.getMessage()));
        });

        app.exception(Exception.class, (e, ctx) -> {
            e.printStackTrace();
            ctx.status(500).json(Map.of(
                "error", "Internal server error",
                "detail", e.getMessage() == null ? "(no message)" : e.getMessage()
            ));
        });

        app.start(port);
        System.out.println("FingerMatcher " + VERSION + " (" + ENGINE + ") ready on port " + port);
    }
}
