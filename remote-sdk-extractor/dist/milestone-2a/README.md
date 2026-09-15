# ROUTE_B_SDK Milestone 2A Package

This package performs runtime/JAR discovery and reflection-only bridge discovery on the remote
Windows machine. It does not connect to CMS, load a universe, copy SAP SDK JARs, retain
credentials, or generate HANA artifacts.

Run the repository entrypoint with the six required paths:

```powershell
.\remote-sdk-extractor\scripts\run-milestone-2a.ps1 `
  -SapInstallRoot 'C:\SAP' `
  -IdtPluginDirectory 'C:\SAP\IDT\plugins' `
  -SapJvmBinDirectory 'C:\SAP\jvm\bin' `
  -LocalIdtProjectDirectory 'C:\IDT\workspace' `
  -WorkingDirectory 'C:\route-b-work' `
  -OutputDirectory 'C:\route-b-output'
```

Outputs are written to `<OutputDirectory>\remote_discovery_output\`. The SAP-supported JVM
version and architecture are detected at runtime; Java 11 is not required by this package.
