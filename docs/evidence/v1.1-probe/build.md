---
title: "Build"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# build verification

Implementation revision: `71522a1351307657a8abe369c841898f254b6152`.

```text
2026-10-02 16:08:38.946 xcodebuild[30736:20906028]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-02 16:08:39.282 xcodebuild[30736:20906026] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
Command line invocation:
    /Applications/Xcode-beta.app/Contents/Developer/usr/bin/xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj -scheme SafeMemoryProbe -sdk iphoneos -configuration Debug -derivedDataPath <derived-data> CODE_SIGNING_ALLOWED=NO build

Build settings from command line:
    CODE_SIGNING_ALLOWED = NO
    SDKROOT = iphoneos26.5

2026-10-02 16:08:39.903 xcodebuild[30736:20906087] CoreSimulatorService connection became invalid.  Simulator services will no longer be available.
2026-10-02 16:08:39.905 xcodebuild[30736:20906113] Logging connecton invalid: <OS_xpc_error: <dictionary: 0x1f9ab40e0> { count = 1, transaction: 0, voucher = 0x0, contents =
	"XPCErrorDescription" => <string: 0x1f9ab4220> { string cache = 0x0, length = 18, contents = "Connection invalid" }
}>
2026-10-02 16:08:39.939 xcodebuild[30736:20906087] Error opening log file (/Users/agent/Library/Logs/CoreSimulator/CoreSimulator.com.apple.dt.xcodebuild.log): Operation not permitted
[-[SimServiceContext sendRequest:]:1751] ERROR : Unable to deliver request ({
    "developer_dir" = "/Applications/Xcode-beta.app/Contents/Developer";
    request = "set_developer_dir";
}) because we are not connected to CoreSimulatorService.
2026-10-02 16:08:39.956 xcodebuild[30736:20906026] [MT] DVTAssertions: Warning in DVTFrameworks/DVTFoundation/FileTypes/DVTFileDataTypeDetection.m:80
Details:  detectedTypeIdentifier (com.apple.binary-property-list) does not conform to matchedTypeIdentifier in MagicFileDataTypeDetector extenson com.apple.property-list. When both are specified, this conformance is required unless overridden by setting allowNonInheritance. extension.identifier:Xcode.MagicFileDataTypeDetector.BinaryPlist
Object:   <DVTFileDataTypeDetectionMagicCache: 0xc80807870>
Method:   -initWithExtension:
Thread:   <_NSMainThread: 0x105451ce0>{number = 1, name = main}
Please file a bug at https://feedbackassistant.apple.com with this warning message and any useful information you can provide.
2026-10-02 16:08:39.957 xcodebuild[30736:20906026] [MT] DVTAssertions: Warning in DVTFrameworks/DVTFoundation/FileTypes/DVTFileDataTypeDetection.m:80
Details:  detectedTypeIdentifier (com.apple.xml-property-list) does not conform to matchedTypeIdentifier in MagicFileDataTypeDetector extenson com.apple.property-list. When both are specified, this conformance is required unless overridden by setting allowNonInheritance. extension.identifier:Xcode.MagicFileDataTypeDetector.XMLPlist
Object:   <DVTFileDataTypeDetectionMagicCache: 0xc808259b0>
Method:   -initWithExtension:
Thread:   <_NSMainThread: 0x105451ce0>{number = 1, name = main}
Please file a bug at https://feedbackassistant.apple.com with this warning message and any useful information you can provide.
[-[SimServiceContext initWithDeveloperDir:connectionType:error:]:432] WARN  : Unable to discover any Simulator runtimes. Developer Directory is /Applications/Xcode-beta.app/Contents/Developer.
[-[SimDiskImageManager init]:175] ERROR : Could not kickstart simdiskimaged; SimDiskImageManager services will not be available: Error Domain=NSPOSIXErrorDomain Code=53 "Software caused connection abort" UserInfo={NSLocalizedDescription=Error returned in reply from CoreSimulatorService: Connection invalid}
[-[SimDiskImageManager _onQueue_checkConnection:]:239] ERROR : simdiskimaged returned error (invalid), marking disconnected.
[-[SimDiskImageManager _onQueue_checkConnection:]:239] ERROR : simdiskimaged returned error (invalid), marking disconnected.
[-[SimServiceContext initWithDeveloperDir:connectionType:error:]_block_invoke:468] ERROR : Could not get list of trusted mount directories: Error Domain=com.apple.CoreSimulator.SimError Code=410 "The service used to manage runtime disk images (simdiskimaged) crashed or is not responding" UserInfo={NSLocalizedDescription=The service used to manage runtime disk images (simdiskimaged) crashed or is not responding}
[-[SimServiceContext sendRequest:reply:error:]:1771] ERROR : Unable to deliver request ({
    request = "notification_subscription";
    "set_path" = "/Users/agent/Library/Developer/CoreSimulator/Devices";
}) because we are not connected to CoreSimulatorService.
2026-10-02 16:08:40.059 xcodebuild[30736:20906028] Error Domain=NSPOSIXErrorDomain Code=61 "Connection refused" UserInfo={NSLocalizedDescription=CoreSimulatorService connection became invalid.  Simulator services will no longer be available.}
[-[SimServiceContext sendRequest:reply:error:]:1771] ERROR : Unable to deliver request ({
    request = "notification_subscription";
    "set_path" = "/Users/agent/Library/Developer/CoreSimulator/Devices";
}) because we are not connected to CoreSimulatorService.
2026-10-02 16:08:40.061 xcodebuild[30736:20906086] Error Domain=NSPOSIXErrorDomain Code=61 "Connection refused" UserInfo={NSLocalizedDescription=CoreSimulatorService connection became invalid.  Simulator services will no longer be available.}
2026-10-02 16:08:40.061 xcodebuild[30736:20906028]  IDESimulatorAvailability: startObservingSimulatorUpdates() FAILED to register SimDeviceSet observer
2026-10-02 16:08:40.061 xcodebuild[30736:20906086]  iOSSimulator: [SimServiceContext defaultDeviceSetWithError:] returned nil (Error Domain=NSPOSIXErrorDomain Code=61 "Connection refused" UserInfo={NSLocalizedFailureReason=Failed to subscribe to notifications from CoreSimulatorService., NSLocalizedDescription=Failed to initialize simulator device set., NSUnderlyingError=0xc80a1ea60 {Error Domain=NSPOSIXErrorDomain Code=61 "Connection refused" UserInfo={NSLocalizedDescription=CoreSimulatorService connection became invalid.  Simulator services will no longer be available.}}}). Simulator device support disabled.
2026-10-02 16:08:40.256 xcodebuild[30736:20906026] [MT] IDERunDestination: Supported platforms for the buildables in the current scheme is empty.
--- xcodebuild: WARNING: Using the first of multiple matching destinations:
{ platform:iOS, id:dvtdevice-DVTiPhonePlaceholder-iphoneos:placeholder, name:Any iOS Device }
{ platform:macOS, arch:arm64, variant:Designed for [iPad,iPhone], id:00008103-000818190E53001E, name:My Mac }
{ platform:iOS Simulator, id:dvtdevice-DVTiOSDeviceSimulatorPlaceholder-iphonesimulator:placeholder, name:Any iOS Simulator Device }
ComputePackagePrebuildTargetDependencyGraph

Prepare packages

CreateBuildRequest

SendProjectDescription

CreateBuildOperation

ComputeTargetDependencyGraph
note: Building targets in dependency order
note: Target dependency graph (1 target)
    Target 'SafeMemoryProbe' in project 'SafeMemoryProbe' (no dependencies)

GatherProvisioningInputs

CreateBuildDescription

ExecuteExternalTool /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc --version

ExecuteExternalTool /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang -v -E -dM -isysroot /Applications/Xcode-beta.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk -x c -c /dev/null

ExecuteExternalTool /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/ld -version_details

Build description signature: a72378a3920034a3b4f72389fe38b872
Build description path: <derived-data>/Build/Intermediates.noindex/XCBuildData/a72378a3920034a3b4f72389fe38b872.xcbuilddata
ClangStatCache /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang-stat-cache /Applications/Xcode-beta.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk <derived-data>/SDKStatCaches.noindex/iphoneos26.5-23F5043e-fdc34335593e8c95adeac9cf6439a1e1.sdkstatcache
    cd <probe-checkout>/connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj
    /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang-stat-cache /Applications/Xcode-beta.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.5.sdk -o <derived-data>/SDKStatCaches.noindex/iphoneos26.5-23F5043e-fdc34335593e8c95adeac9cf6439a1e1.sdkstatcache
Failed to create FS event stream. Considering the cache up-to-date.

ProcessInfoPlistFile <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/Info.plist <derived-data>/Build/Intermediates.noindex/SafeMemoryProbe.build/Debug-iphoneos/SafeMemoryProbe.build/empty-SafeMemoryProbe.plist (in target 'SafeMemoryProbe' from project 'SafeMemoryProbe')
    cd <probe-checkout>/connectors/ios/SafeMemoryProbe
    builtin-infoPlistUtility <derived-data>/Build/Intermediates.noindex/SafeMemoryProbe.build/Debug-iphoneos/SafeMemoryProbe.build/empty-SafeMemoryProbe.plist -producttype com.apple.product-type.application -genpkginfo <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/PkgInfo -expandbuildsettings -format binary -platform iphoneos -requiredArchitecture arm64 -o <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/Info.plist

CopySwiftLibs <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app (in target 'SafeMemoryProbe' from project 'SafeMemoryProbe')
    cd <probe-checkout>/connectors/ios/SafeMemoryProbe
    builtin-swiftStdLibTool --copy --verbose --scan-executable <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/SafeMemoryProbe.debug.dylib --scan-folder <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/Frameworks --scan-folder <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/PlugIns --scan-folder <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/SystemExtensions --scan-folder <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/Extensions --platform iphoneos --toolchain /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain --destination <derived-data>/Build/Products/Debug-iphoneos/SafeMemoryProbe.app/Frameworks --strip-bitcode --strip-bitcode-tool /Applications/Xcode-beta.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/bitcode_strip --emit-dependency-info <derived-data>/Build/Intermediates.noindex/SafeMemoryProbe.build/Debug-iphoneos/SafeMemoryProbe.build/SwiftStdLibToolInputDependencies.dep --filter-for-swift-os --back-deploy-swift-span
Ignoring --strip-bitcode because --sign was not passed

** BUILD SUCCEEDED **


```
