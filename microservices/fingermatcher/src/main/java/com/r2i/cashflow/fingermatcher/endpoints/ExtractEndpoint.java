package com.r2i.cashflow.fingermatcher.endpoints;

import com.fasterxml.jackson.databind.JsonNode;
import com.machinezoo.sourceafis.FingerprintImage;
import com.machinezoo.sourceafis.FingerprintImageOptions;
import com.machinezoo.sourceafis.FingerprintTemplate;
import io.javalin.http.Context;

import java.util.Base64;
import java.util.Map;

/**
 * POST /extract
 *
 * Request:  { "image_b64": "...", "image_format": "png" | "bmp" | "raw_grayscale" }
 * Response: { "template_b64": "...", "quality_score": 0-100, "minutiae_count": N }
 *
 * Errors:
 *   400 - imagen mal formada o base64 invalido
 *   422 - imagen sin minucias suficientes para template fiable
 */
public class ExtractEndpoint {

    private static final int MIN_MINUTIAE = 12;
    private static final int QUALITY_FULL_MINUTIAE = 60;

    public static void handle(Context ctx) {
        JsonNode body = ctx.bodyAsClass(JsonNode.class);
        if (!body.has("image_b64")) {
            throw new IllegalArgumentException("Missing field: image_b64");
        }

        String imageB64 = body.get("image_b64").asText();
        byte[] imageBytes;
        try {
            imageBytes = Base64.getDecoder().decode(imageB64);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("Invalid base64 in image_b64");
        }

        // SourceAFIS recomienda especificar DPI explicito (no es scale-invariant).
        // DigitalPersona U.are.U 4500 captura a 500 DPI nativos.
        FingerprintImageOptions options = new FingerprintImageOptions().dpi(500);
        FingerprintImage image;
        try {
            image = new FingerprintImage(imageBytes, options);
        } catch (Exception e) {
            throw new IllegalArgumentException("Image not recognized or unprocessable: " + e.getMessage());
        }

        FingerprintTemplate template;
        try {
            template = new FingerprintTemplate(image);
        } catch (Exception e) {
            ctx.status(422).json(Map.of(
                "error", "Could not extract template from image",
                "detail", e.getMessage() == null ? "" : e.getMessage()
            ));
            return;
        }

        byte[] templateBytes = template.toByteArray();

        // Heuristica de quality basada en tamano del template serializado.
        // CBOR template ~ 10 bytes por minucia + ~100 bytes overhead.
        // Aproximacion suficiente para v1; refinar con transparency API si hace falta.
        int approxMinutiaeCount = Math.max(0, (templateBytes.length - 100) / 10);
        int qualityScore = Math.min(100, Math.max(0, approxMinutiaeCount * 100 / QUALITY_FULL_MINUTIAE));

        if (approxMinutiaeCount < MIN_MINUTIAE) {
            ctx.status(422).json(Map.of(
                "error", "Insufficient minutiae extracted",
                "minutiae_count", approxMinutiaeCount,
                "quality_score", qualityScore
            ));
            return;
        }

        ctx.json(Map.of(
            "template_b64", Base64.getEncoder().encodeToString(templateBytes),
            "quality_score", qualityScore,
            "minutiae_count", approxMinutiaeCount
        ));
    }
}
