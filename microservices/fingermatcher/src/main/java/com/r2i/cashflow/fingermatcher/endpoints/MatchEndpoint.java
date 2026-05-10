package com.r2i.cashflow.fingermatcher.endpoints;

import com.fasterxml.jackson.databind.JsonNode;
import com.machinezoo.sourceafis.FingerprintMatcher;
import com.machinezoo.sourceafis.FingerprintTemplate;
import io.javalin.http.Context;

import java.util.Base64;
import java.util.Map;

/**
 * POST /match
 *
 * Request:  { "template_a_b64": "...", "template_b_b64": "..." }
 * Response: { "score": 64.3 }
 *
 * Errors:
 *   400 - templates mal formados o no deserializables
 */
public class MatchEndpoint {

    public static void handle(Context ctx) {
        JsonNode body = ctx.bodyAsClass(JsonNode.class);
        if (!body.has("template_a_b64") || !body.has("template_b_b64")) {
            throw new IllegalArgumentException("Missing fields: template_a_b64 and/or template_b_b64");
        }

        FingerprintTemplate templateA = deserialize(body.get("template_a_b64").asText(), "template_a_b64");
        FingerprintTemplate templateB = deserialize(body.get("template_b_b64").asText(), "template_b_b64");

        double score = new FingerprintMatcher(templateA).match(templateB);

        ctx.json(Map.of("score", score));
    }

    private static FingerprintTemplate deserialize(String b64, String fieldName) {
        byte[] bytes;
        try {
            bytes = Base64.getDecoder().decode(b64);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("Invalid base64 in " + fieldName);
        }
        try {
            return new FingerprintTemplate(bytes);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid template in " + fieldName + ": " + e.getMessage());
        }
    }
}
