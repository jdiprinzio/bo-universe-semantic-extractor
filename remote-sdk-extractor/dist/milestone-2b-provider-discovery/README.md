# ROUTE_B_SDK Milestone 2B Provider Discovery

Reflection-only discovery of read-only provider methods returning `DataSource` or
`DataFoundation`. This package does not connect to CMS, retrieve resources, instantiate SDK
objects, or generate HANA artifacts.

PowerShell only compiles and launches; JAR discovery, filtering, class enumeration,
reflection, progress logging, and diagnostics all run inside the single Java process.

Run from any directory on the remote BusinessObjects machine:

```powershell
.\run-provider-discovery.ps1 `
  -SapInstallRoot 'C:\Program Files\SAP BusinessObjects' `
  -IdtPluginDirectory 'C:\Program Files\SAP BusinessObjects\Information Design Tool\plugins' `
  -SapJvmBinDirectory 'C:\path\to\sap-supported-jvm\bin' `
  -WorkingDirectory 'C:\route-b-work' `
  -OutputDirectory 'C:\route-b-output'
```

