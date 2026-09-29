# Preparing a case

This release reads prepared JSON, not original customer documents. An engineer must first decide whether the seven formulas in WORLD_CONTRACT.md fit the intended scope. One camera family and additive timestamp offsets are the permitted change model. Clock-rate conversion, camera/lighting redesign and unmodeled physical requirements do not become supported by supplying extra numbers.

`case.json` carries `case_id`, `variant_ids`, `candidate_camera_ids`, `base_firmware_revision` and `source_inventory` entries (`source_id`, relative `path`). Each inventory file carries matching `source_id`, `kind`, `status`, optional/required-as-applicable `subject_id`, `revision`, `supersedes`, and `data`. Use the complete example as a starting point; the loader is implemented in `sources.py`.

- Preserve the original documents separately. For each numerical field record its original locator, unit, revision, authority, operating conditions and observation-versus-guarantee status in your preparation record.
- `active` alone does not make a newer revision authoritative. Only explicit active same-subject supersession retires its predecessor. Conflicting active leaves remain unknown. Missing `subject_id` remains unassociated.
- Use null for unknown bounds. Typical values and sample maxima are not guaranteed bounds. The program cannot detect a human incorrectly entering an observation in a guarantee field.
- Units are part of the contract: milliseconds, m/s, millimetres and decimal MB/s. Establish timestamp event meaning and clock domain before conversion. The application does not infer them from a datasheet.
- Saved test configuration must identify the variant, camera, specification source, firmware, policy and offset, plus any other relevant configuration fields. The program can compare supplied fields only.
- Costs are synthetic points. Unknown cost is unranked. Any real economic interpretation requires a separate explicit agreement.
- A `firmware` record's `file_reference` in the example points to bundled illustrative source relative to that case. The application never executes input firmware. It emits its own small proposed adapter only when a plan is justified.

Use contained relative inventory paths. The loader rejects malformed JSON, duplicate keys, nonfinite values, prohibited numeric booleans, identity mismatches, path escapes and invalid numerical domains. This is structural validation, not proof that a real source was interpreted correctly.

The HTML displays source identifiers and JSON locators as text. It does not provide a document-management or provenance-authentication service. Retain your source packet and reviewer dispositions alongside the generated output.
