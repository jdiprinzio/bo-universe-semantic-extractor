# Milestone 2A Remote Runbook

Milestone 2A performs runtime discovery and loading-bridge discovery only. It does not connect
to CMS, retrieve a universe, load BLX/DFX resources, or generate HANA artifacts.

## Remote Windows Command

Run from the repository root on the Windows machine containing the SAP-supported BusinessObjects
client runtime and SDK JARs:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Set-Location C:\path\to\bo-universe-semantic-extractor
$env:JAVA_HOME = 'C:\path\to\sap-supported-jvm'
.
remote-sdk-extractor\scripts\run-milestone-2a.ps1 `
  -SapInstallRoot 'C:\Program Files\SAP BusinessObjects' `
  -IdtPluginDirectory 'C:\Program Files\SAP BusinessObjects\Information Design Tool\plugins' `
  -SapJvmBinDirectory 'C:\path\to\sap-supported-jvm\bin' `
  -LocalIdtProjectDirectory 'C:\IDT\workspace' `
  -WorkingDirectory 'C:\route-b-work' `
  -OutputDirectory 'C:\route-b-output'
```

The command validates `java.exe`, `javac.exe`, `javap.exe`, and `jar.exe`; detects JVM version,
JVM architecture, and OS architecture; inventories external SAP JARs; validates every class in
`config/route_b/confirmed_sdk_capabilities.json`; discovers candidate DataSource/DataFoundation/
BusinessLayer classes; runs `javap`; compiles and executes a reflection-only probe; and writes
`C:\route-b-output\remote_discovery_output\`.

## Expected Output

```text
sdk_environment.json
sdk_jar_inventory.json
validated_capabilities.json
candidate_loading_services.json
javap_method_inventory.txt
loading_bridge_probe.json
loading_bridge_findings.json
execution_report.md
hashes.sha256
export_manifest.json
```

## Security and Transfer

- The SAP SDK classpath is external and no JAR is copied into the repository or package.
- No credentials, CMS session files, UNX/BLX/DFX/CNS resources, or HANA artifacts are accepted
  as package contents.
- The probe uses class loading/reflection only and hard-codes `cms_connection_attempted=false`.
- Transfer only the sanitized `remote_discovery_output` directory after reviewing
  `sdk_jar_inventory.json` paths and `hashes.sha256`.
- Do not run a CMS retrieval command as part of Milestone 2A.

## Failure Codes

The runner fails with structured codes for missing Java tools, missing SDK JARs, missing confirmed
classes, classpath failures, malformed capability/probe output, and architecture mismatch.
