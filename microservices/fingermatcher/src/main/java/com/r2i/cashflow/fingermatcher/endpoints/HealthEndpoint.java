package com.r2i.cashflow.fingermatcher.endpoints;

import com.r2i.cashflow.fingermatcher.FingerMatcherApp;
import io.javalin.http.Context;

import java.util.Map;

public class HealthEndpoint {

    public static void handle(Context ctx) {
        long uptimeMs = System.currentTimeMillis() - FingerMatcherApp.STARTUP_TIME_MS;
        ctx.json(Map.of(
            "status", "ok",
            "version", FingerMatcherApp.VERSION,
            "engine", FingerMatcherApp.ENGINE,
            "uptime_seconds", uptimeMs / 1000
        ));
    }
}
