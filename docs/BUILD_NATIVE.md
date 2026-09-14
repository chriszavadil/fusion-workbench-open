# Build the native Windows application

Install Unreal Engine 5.7 with a supported Visual Studio 2022 C++ toolchain and
Windows SDK. The verified build used UE 5.7.3, MSVC 14.44 and SDK 10.0.22621.0.
Do not use an older C++ linker with engine libraries requiring newer runtime symbols.
Engine source, compiler tools and SDKs are not included in this repository.

The project is native/FusionWorkbench.uproject. The native C++ Slate interface
reads Content/WorkbenchData/catalog.json and the two FWB1 display-mesh files.
Their metres-to-centimetres conversion and independent model identities are tested.
The shipped Content assets are original generated materials and an empty boot map.
They can be regenerated using create_native_assets.py through editor scripting.
export_native_meshes.py exports the original Blender scenes into the bounded
runtime mesh format; the browser still uses glTF from the same display models.

Use Unreal's normal Windows Shipping Build/Cook/Stage/Package pipeline.
The app needs no editor or Python merely to view models and replay records.
For a local runtime check, launch the packaged executable with
`-WorkbenchSelfTest -WorkbenchScreenshot -windowed`.
After configuring and starting the reviewed local worker, the explicit
`-WorkbenchSolverSmokeTest` option submits one approved full-system reproduction.
Do not run these flags against a worker that is already handling another experiment.

Generated validation outputs stay in the local Saved directory, not public source.
A passing software check is not experimental validation. Do not publish raw
Windows logs, PDB symbols, local execution configuration or developer caches.
