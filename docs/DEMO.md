# Demonstration: evaluate, then identify useful evidence

The bundled scenarios are synthetic and user-prepared. No supplier or hardware claim is authenticated.

1. Run `python3 -B app.py analyze --case examples/public_camera_change --out outputs/demo-review` and open its engineering_review.html. The established plan is CAM-B/per_variant at five synthetic points.
2. Run `python3 -B app.py questions --case examples/public_camera_change --camera CAM-D --out outputs/demo-question`. Open explanation.md. Both policy domains include guaranteed jitter j <= 2/5 ms (0.4 ms). Shared costs two points; per_variant costs five. Read the cited source, revision, field and variant conditions. The typical value and saved sample are insufficient.
3. Run `python3 -B app.py questions --case examples/blocked_camera_change --camera CAM-D --out outputs/demo-blocked`. CAM-D power is stipulated as 11 W. The fast variant permits 10 W. The method identifies the failure and withholds a jitter-only sufficient evidence request.

Saved outputs from these last two commands are in demonstrations/public and demonstrations/blocked, alongside their exact result.json files. They are actual author-run outputs, not screenshots or reconstructed claims. Their source_sha256 entries bind the case files used. Only the blocked case ID and CAM-D power differ from the public case.

The ordinary review remains available as example_review.html. Re-running the original public case reproduced it byte for byte.

The value being demonstrated is actionable conditional analysis: which missing guarantee could change the selected option, and when it cannot help alone. No guarantee is obtained, input rewritten, configuration deployed, or savings measured. The new command emits no firmware/configuration. Each invocation captures its own inputs; freeze a copied case for a multi-command presentation.
