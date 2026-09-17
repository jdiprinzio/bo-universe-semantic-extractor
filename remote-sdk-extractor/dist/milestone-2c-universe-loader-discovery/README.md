# ROUTE_B_SDK Milestone 2C Universe Loader Discovery

Reflection-only discovery of methods that return `com.businessobjects.mds.universe.Universe`
(or a subtype), classified by input signature, plus an inventory of methods returning or
accepting `com.businessobjects.mds.repository.DataFoundationFile`. This package does not
connect to CMS, retrieve resources, instantiate SDK objects, or write anything.

PowerShell only compiles and launches; JAR discovery, filtering, class enumeration,
reflection, progress logging, and diagnostics all run inside the single Java process.

Run from any directory on the remote BusinessObjects machine:

```powershell
.\run-universe-loader-discovery.ps1 `
  -SapInstallRoot 'C:\Program Files\SAP BusinessObjects' `
  -IdtPluginDirectory 'C:\Program Files\SAP BusinessObjects\Information Design Tool\plugins' `
  -SapJvmBinDirectory 'C:\path\to\sap-supported-jvm\bin' `
  -WorkingDirectory 'C:\route-b-work' `
  -OutputDirectory 'C:\route-b-output'
```

Outputs are written under `<OutputDirectory>\universe_loader_discovery\`:
`universe_providers.json`, `file_based_loaders.json`, `datafoundation_file_methods.json`,
`target_class_load_verification.json`, `execution_report.md`, `discovery_progress.log`.
