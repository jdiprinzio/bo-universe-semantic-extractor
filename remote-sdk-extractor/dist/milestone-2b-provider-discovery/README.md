# ROUTE_B_SDK Milestone 2B Provider Discovery

Reflection-only and javap-only discovery of read-only provider methods returning `DataSource` or
`DataFoundation`. This package does not connect to CMS, retrieve resources, instantiate SDK
objects, or generate HANA artifacts.

Run from any directory on the remote BusinessObjects machine:

```powershell
.\run-provider-discovery.ps1 `
  -SapInstallRoot 'C:\Program Files\SAP BusinessObjects' `
  -IdtPluginDirectory 'C:\Program Files\SAP BusinessObjects\Information Design Tool\plugins' `
  -SapJvmBinDirectory 'C:\path\to\sap-supported-jvm\bin' `
  -LocalIdtProjectDirectory 'C:\IDT\workspace' `
  -WorkingDirectory 'C:\route-b-work' `
  -OutputDirectory 'C:\route-b-output'
```
