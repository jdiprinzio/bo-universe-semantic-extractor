# Milestone 2A Patch Release 10 Report

## Schema Alignment Fix

`Milestone2aProbe` now parses the actual capability contract shape:

```json
{
  "capabilities": [
    {"class": "fully.qualified.ClassName"}
  ]
}
```

Parsing is whitespace-tolerant and scoped to `capabilities[*].class`; it no longer searches for
the narrower invalid pattern `"class":"..."`. Empty arrays and missing capability arrays fail
with actionable malformed-input errors. Every extracted class is then loaded reflectively and
included in `validated_capabilities.json` through the existing probe output.

## Tests

- Capability parsing with whitespace and multiple class entries: covered.
- Confirmed class loading: covered with `java.lang.String` and `java.lang.Integer`.
- Empty capability array: covered and fails clearly.
- Malformed schema without `capabilities`: covered and fails clearly.
- Focused Route B tests: **17 passed** after the patch.
- Full Python suite: **137 passed** after the patch.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.
