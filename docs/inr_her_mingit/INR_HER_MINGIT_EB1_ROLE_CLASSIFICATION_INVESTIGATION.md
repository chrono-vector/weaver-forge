# INR-HER MinGit EB-1 Static Role Classification Investigation

Status: DOCUMENTATION_ONLY_CLASSIFICATION_PROPOSAL
Date: 2026-10-11 (Asia/Tokyo)

## Scope and retained baseline

This is a new investigation report, not a Human Final, ratification, operational manifest, binding decision, or independent reproduction.
BASELINE_VERIFIED and ZIP_SIZE_AND_SHA256_VERIFIED are accepted user-provided prior results, not repeated measurements.
Existing inventory: C:/Users/mine0/AppData/Local/Temp/weaver-forge-mingit-evidence/613673731/MINGIT_613673731_FILE_MEMBER_INVENTORY.json.
Existing retained distribution: MinGit-2.56.0.2-64-bit.zip, asset 613673731.
The recorded distribution digest is da35e72aa21c005a5a0d298cfbae110bc1609a815730ea0dde84b01a1b3cd3be; it was copied, not recomputed.
All member SHA-256 values below are copied from the existing inventory. No new member hash, ZIP hash, size, or inventory measurement was performed.

Selected candidate: ucrt64/bin/git.exe (existing recorded digest b824434dfe3b5f9cf648af6c9cc8cb1f6a982cc6e13b6c6ebbe6533c7e51cc2e).
Excluded execution target: cmd/git.exe (existing recorded digest 54bda91c773c6bba2b970424423cfcb80552d92dc6967d766f98931fe1251a54).
Both retain their existing lexical classification and are excluded from the 371-row proposal. No binary was executed.

## Counts and decision rule

- Existing inventory rows: 373.
- Previously identified candidate/shim rows: 2.
- Remaining rows considered: 371.
- Definitive dependency proposals: 0.
- Definitive other proposals: 0.
- Retained UNRESOLVED classifications: 371.
- Within UNRESOLVED, static dependency candidates: 4.
- Within UNRESOLVED, files without established reach or exclusion: 367.

A static import name is evidence of a dependency request, not proof that the Windows loader selects the same-named distribution member. Four files therefore have a dependency hypothesis while remaining UNRESOLVED. No filename, extension, absence from native import descriptors, or apparent documentation/license location proves that a file is irrelevant to execution. No item is assigned other solely on those grounds.
UNRESOLVED is an EB-1 research label, not an allowed EB-0 manifest role. This report must not be supplied as a complete EB-0 manifest or used to claim dependency closure.

## Static analysis method and scope

Read the existing ZIP in memory only to inspect PE import descriptors of the selected image and recursively encountered unique ucrt64/bin members. Nothing was extracted or installed. Used Python standard-library zipfile and struct; no tools or dependencies were installed.
The PE walk checked MZ and PE signatures, PE32/PE32+ optional-header layout, section RVA-to-file mapping, data-directory counts, normal imports (directory 1), delay imports (directory 13), and null-terminated descriptor/name fields. Unsupported VA-based delay descriptors would remain unresolved. No normal/delay parser errors were reported for the five inspected members. No delay import edge was observed in those five files.
This is a bounded inspection using an ad hoc parser, not independently validated complete PE analysis. It does not resolve Windows API sets, forwarded exports, SxS, DLL search order, dynamically computed LoadLibrary/GetProcAddress calls, imported helper commands, scripts, configuration, TLS resources, plugins, managed assemblies, or operation-specific behavior.

Direct ordinary import requests in ucrt64/bin/git.exe identify libiconv-2.dll, libintl-8.dll, libpcre2-8-0.dll, and zlib1.dll. The inventory provides one matching packaged basename for each, in ucrt64/bin. libintl-8.dll additionally imports libiconv-2.dll. These concrete import edges, not extensions, support the four dependency hypotheses.
Native/system import names absent from the ZIP are listed below. Their absence is not an error verdict and does not prove safe resolution or justify exclusion from the trust boundary.

- ADVAPI32.dll
- KERNEL32.dll
- USER32.dll
- WS2_32.dll
- api-ms-win-crt-convert-l1-1-0.dll
- api-ms-win-crt-environment-l1-1-0.dll
- api-ms-win-crt-filesystem-l1-1-0.dll
- api-ms-win-crt-heap-l1-1-0.dll
- api-ms-win-crt-locale-l1-1-0.dll
- api-ms-win-crt-math-l1-1-0.dll
- api-ms-win-crt-private-l1-1-0.dll
- api-ms-win-crt-process-l1-1-0.dll
- api-ms-win-crt-runtime-l1-1-0.dll
- api-ms-win-crt-stdio-l1-1-0.dll
- api-ms-win-crt-string-l1-1-0.dll
- api-ms-win-crt-time-l1-1-0.dll
- api-ms-win-crt-utility-l1-1-0.dll
- ntdll.dll

## Evidence codes

- S1: Selected Git PE contains the named ordinary import; unique packaged basename exists in ucrt64/bin. Candidate dependency only; real loader resolution and full closure unproven.
- S2: Same S1 evidence plus libintl-8.dll transitively imports this name.
- U1: Existing inventory establishes packaged path and previously recorded digest only. No positive dependency or operation-specific exclusion evidence established in this scope; maintain UNRESOLVED.

## Per-file classification proposal

| Relative path | Existing inventory SHA-256 (copied) | Classification | Hypothesis | Evidence |
|---|---|---|---|---|
| cmd/git-receive-pack.exe | e17fb061f4b959136bd4db893637ba99eaec7452b242d11be6f1109417fda51e | UNRESOLVED | unestablished | U1 |
| cmd/git-upload-pack.exe | e0c90ab1f94903b407090a27469c70b8b4eb4014706292d60285de08a82d61b8 | UNRESOLVED | unestablished | U1 |
| cmd/scalar.exe | 54bda91c773c6bba2b970424423cfcb80552d92dc6967d766f98931fe1251a54 | UNRESOLVED | unestablished | U1 |
| etc/bash.bashrc | 2d6e33b3e892e2b4abf9079eaac95da0fe3875e325a0c34dc566d15957df3037 | UNRESOLVED | unestablished | U1 |
| etc/fstab | 50718b489a9ef0d4590ef6725f903166c50b6291fb1d9a8c86ff8d221b921aea | UNRESOLVED | unestablished | U1 |
| etc/gitattributes | a952eb8d7f2edeb08eac68b36ebd5d888bce3541aa458a9e38af337a4f1fe110 | UNRESOLVED | unestablished | U1 |
| etc/gitconfig | 4b27ceb03e73554574a61d336a1d1af680be285d9ca0ad51814b89dd464c1413 | UNRESOLVED | unestablished | U1 |
| etc/libexec-moved.txt | 43e4ff410191758bebb48559de611138f73b692ad38777c9ae41b333f9ca15ea | UNRESOLVED | unestablished | U1 |
| etc/msystem | 74bd56de00e49c3917deca2ede723eecd1312a86357b100ae8aabd219f6e7d5e | UNRESOLVED | unestablished | U1 |
| etc/msystem.d/CLANG64 | f2b01902f08feb07fed47f5ffea3462764034abc19e9ddf3aa6f20f93afeaab6 | UNRESOLVED | unestablished | U1 |
| etc/msystem.d/CLANGARM64 | 82859ae69d40de560d03c0a59e38e8b3405293003c1d24237f6bbd5efe3c87ef | UNRESOLVED | unestablished | U1 |
| etc/msystem.d/MINGW32 | 809ff47346e21e0e1d285e64f3e0975e7345e311e98bb4e100c8da15e1426d9b | UNRESOLVED | unestablished | U1 |
| etc/msystem.d/MINGW64 | 879495ad6b15f59ec2057551e06fb2917715c66de80f5bf915d6176d78e50eee | UNRESOLVED | unestablished | U1 |
| etc/msystem.d/MSYS | b166ab9772874471695f5beb16f5c39b6207c937353d0aa9079cbe756432df1d | UNRESOLVED | unestablished | U1 |
| etc/msystem.d/UCRT64 | 240fa8efb6fe4b7dae826f5f6d481e41a09913462fe61b5a4ff036d6daa7a835 | UNRESOLVED | unestablished | U1 |
| etc/nsswitch.conf | 0823a988d6c923855be5565bed6f1900e1899ee60513a58ad550389bed276f14 | UNRESOLVED | unestablished | U1 |
| etc/package-versions.txt | 17e1ee29212a294f0bc384bd322b64893a6f9c7b6f8eeec1809272c2cfc8d13c | UNRESOLVED | unestablished | U1 |
| etc/post-install/99-post-install-cleanup.post | 683ab066be19cb4defec470ebd53f165ca5dbf761fd40c13aee8abe31ba42803 | UNRESOLVED | unestablished | U1 |
| etc/profile | 0052386cec2a94dedc0cb11f59da6e64ca8e26289edf935a7d9b9d5d2a87c902 | UNRESOLVED | unestablished | U1 |
| etc/profile.d/bash_profile.sh | 02d38e480a1ec4227e94a5aa073945901680aa3387e3386f8b77f10426ebbc75 | UNRESOLVED | unestablished | U1 |
| etc/profile.d/lang.sh | 6c0ca979c7b146b3750103b1296a399764f4e1b222ee091d3aa072b6da16c1a5 | UNRESOLVED | unestablished | U1 |
| etc/ssh/moduli | 1d89ab9d686ceada1f7869cb7cbf2d3ef041f5054bc148ffa182b6f718e15c81 | UNRESOLVED | unestablished | U1 |
| etc/ssh/sshd_config | 251ea9d27e7526eeba8cf39126ac77d3499c90957a1c34eaca469d0bf5f4dceb | UNRESOLVED | unestablished | U1 |
| etc/ssh/ssh_config | 79ab6dad83c34d9b5c40aaf894d1e0f5cb191f5962d945772d22e2b3668e06d2 | UNRESOLVED | unestablished | U1 |
| LICENSE.txt | 454649ddc02b5cc098513cea28db6592b45ac0a906386287c4d48cf8dbde651c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Atlassian.Bitbucket.dll | 3a9dd735b3e0fc2e4b3f83ed94d11cbfe3e72b86e0a957a0c419f90ce12ab5f4 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Base.dll | ce1eda48b18fb19653e1a6c9a88dec3d9a5c6abd4f06bfd677c410b0de308a24 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Controls.dll | 40c47e611b9f95b32bbf0a6d95c6d84fc89507502a20d21fdb71edecbe77e17a | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.DesignerSupport.dll | 934339931173fcd6d6d1654e05b428b539ef341f7ca4e5acb4da734e0c2795ca | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Dialogs.dll | 747f439687eccf7e1118b1f127aa03f5bb22142d68cd6cec41d628eee85a2a71 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.dll | 06de78055dd7f7705a5514456a34b47bf52d1c8815c34149a4e5a4dfd376aadf | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Markup.dll | 5d07211022aff0ec79716ed7ba6f5cada7b42a0214fd17fd8cc6f9251a1b9e10 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Markup.Xaml.dll | 177df637eaf4e7ee5bad8b0d2d23db33e289035178bd2f3d2b505f62d69b383e | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Metal.dll | 5ee3b9609227895cafd3cc8ea4928f64a29ab1a8be3d0d279db10b430c518063 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.MicroCom.dll | 4a5074ccd8356f99e50b123f64ac846e491f543fa602eb965ef6666089f624b3 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.OpenGL.dll | 9e76ad1503760dae0437abc5352c82cf247209af34cfe5037400065d45474b45 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Remote.Protocol.dll | 9d4b55a9aa9f8e8dd487e53c909d7f552319fc19df9b6734ee1344c229d5dcfe | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Skia.dll | ce8e860f42018a6c319402ae2c6e43a8dbbe52754a203265ce5b356c4a98781e | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Themes.Fluent.dll | eb8e4ead3446893a2382ca08e2769274cd2eb27763c40af7f30e0f135928c997 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Vulkan.dll | 9f726db10a8e4f1615c36092dba406e2bced5ae44759225fc444ea64a4a3e674 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Avalonia.Win32.dll | 65c2e5dbf921a953797b9332280c3c3220c53ebae635ecb96b5de0395d969114 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/av_libglesv2.dll | a5e15a6b84c938c23816ed78475294bc28994582c3659965abc6ca3dceac8fed | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/blocked-file-util.exe | 6571b704559168974e845c6677b2f6974c41770e657b7d8e67931395d70a5982 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/brotli.exe | 5b60e2138ca183792eda3b646f719a5eb5e6851bd10846f0c7686953fc4a9178 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/c_rehash | 0fff99b08ff92806e9676ac142db241bd03580aa4576753b0474be5246c04aa6 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/docx-strip-pii.exe | 8c5baae2d1030018844341ad1ca26619d6ccef425000db6faa68a6a9c5fa29a0 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/docx2txt.exe | 0a7ecd6a21b3ad1798e557861f1143977c586b872c55ea894685d3c6d94627ab | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/gcmcore.dll | cb6a89c6f288117da4b77a902505643230b9e3cdba48cfe88719112a51da0690 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-askpass.exe | b8c5202c86d67907737b4ff261b8323f56e919802981ea3068072bde361bc417 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-askyesno.exe | 02579d76d62a236b2c02e0cc0bf59d123bbc57fb9ceee56dfccdeaaba7b096f1 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-credential-helper-selector.exe | 56d2b197be634d2d605ff90575a1d274b4e777994ca194c6ecf78affd0841aaa | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-credential-manager.exe | a1e4f00c79b0c9c7f087e72eed50a892e833bdd403652f2b40da86e81f27e9dd | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-credential-manager.exe.config | a64e209b9476be9acb9e4a3b7813e0ba48321ae2da1b675cd584f5319dc0c66f | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-http-fetch.exe | 004198670100b322692da8d84e7b31e94ccec18ad8d19b482b7cea58b1fbf3cb | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-http-push.exe | 5bd3908f1be21ef6553e8f09d25a6af979f908d948543bb2b78d327242aa0bce | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-receive-pack.exe | 9af8b86cb229e389829f579136c0baad689aba575e332b05731dd6efabe27a1b | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-remote-http.exe | 9af8b86cb229e389829f579136c0baad689aba575e332b05731dd6efabe27a1b | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-remote-https.exe | cff545e0d31b555cc1c5235785626dbb804eeae212f8f0f829b32fb30b7dec90 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-sh-i18n--envsubst.exe | d8ab9f16566d860bcbb7584f0c697ba4b7e5abf7b75f69d4c2fa8e6a4738d3f5 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-update-git-for-windows | 8120b41b869693e07acc4707a0ab45505e7c5e4156a3a44b19152f1f425df85f | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/git-upload-pack.exe | 9af8b86cb229e389829f579136c0baad689aba575e332b05731dd6efabe27a1b | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/GitHub.dll | e84351b4f90169c001ec2f88889a731308f286612dd03c7a2526ad013266fc8d | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/GitLab.dll | c87e5ee958cf609ef4c2a027d12659d1e2c1ec7efcc7dbc15c9ec4518e4860f0 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/HarfBuzzSharp.dll | d37714e703cfd98fcabd01cf495a66c0acf5f99bc78c5372ff4752632deddb1e | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/headless-git.exe | 587ce3c5b305dd1a8a4aa3aa79597693b29fc10b40e0b6398e53b9eaf06413b4 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libbrotlicommon.dll | c62c08223e450dfc2fff33c752cc228505ffd9d755201958ba800d5d30481a2c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libbrotlidec.dll | e270b6e576594ee8ee6e33ccc54e34a54304616dd6225652e11e49d6f17ef896 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libbrotlienc.dll | 82573820fe9cc3f57004b6603428e2fa1bfc9d2048707bfcead3cfc5ef3ab284 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libcrypto-3-x64.dll | f8839fd7d5b5e7b1763c88705538c5762a2f97df17f37092e37de3c663f30b1e | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libcurl-4.dll | 372306ee48ffe79b2edc6d8b07d9d60dee0f016c73faaca0dffe4e926f6f1220 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libcurl-openssl-4.dll | 1359edc75197a1db4a3c5402cdb0a625927b8ddcb97fd62ac57d8e14d306bc55 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libexpat-1.dll | 228d7458da0d55a060a982ae809503f2ea9bdfc6f88b9fa756abb98ffe04afa8 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libHarfBuzzSharp.dll | 8449848dd71c47bebfb16892d56918f2e26706d67138133fdb940831fd9f09e3 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libiconv-2.dll | 94ec68fb8d342b6c91b6b48a8d95092819cdcd006a7166e0b68062f946afd08a | UNRESOLVED | dependency candidate | S2 |
| ucrt64/bin/libidn2-0.dll | a054a6bb69aaf4666157f968740412e9697085cbc1e48a78f8dd9622169c5aaf | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libintl-8.dll | 0e5a178731e6be6d115442a6ade3df7f03265cd1fc4338f8b6f86a8001cbf582 | UNRESOLVED | dependency candidate | S1 |
| ucrt64/bin/libnghttp2-14.dll | 550b9933ce54833ebb2c0e24b43e1463006c6c62305c471570c6bf18095581bd | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libpcre2-8-0.dll | 1f609cde2ce432efb7d2b0c7b84a14a6dbfc9622d1ac1a3cbadf51c5b0b4dada | UNRESOLVED | dependency candidate | S1 |
| ucrt64/bin/libpsl-5.dll | a531e72de3c64d43fb83cbfb6fa63e5ee982a970292ec51314e29d0acabf1dd5 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libSkiaSharp.dll | 8dc867e29f3dacca41e15af5d557542f4982c59f770ba6ac811ed6026fd2874e | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libssh2-1.dll | a0e7eea75814708ce5c9b2a83998b14ac1268b70cccc2c22686f4ab585a3aac1 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libssl-3-x64.dll | 6af55a4d522e2cc29ff0833cad4f6f7560f8ba2d107b97990d9415c590a4224a | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libunistring-5.dll | ee39258fa1086269674a8179d3cfaf7c4e380ada14441b5dd9ed53d82d15c4e3 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/libzstd.dll | 48368ab0ca622d0ec12f41ce85d91f22866bf5da92c77a69a06483564c93816c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/MicroCom.Runtime.dll | 67fcbaa2bd582e79e2f3646c1a43bb86676a096cb17729cf946f69a5c07abaeb | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.AzureRepos.dll | 3e7965775aa78682af5b0dce2516c5b1abd8b96d6af9419f540b7f17f66be5d6 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.Bcl.AsyncInterfaces.dll | 18940307939380c25f2ea6467d9846bba566438320740fdd4c31184be46b709d | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.Identity.Client.Broker.dll | 2fa5fc6cfa093bb1cd9d67e2783212ccce0606987c043add43e588e93e5e51f4 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.Identity.Client.dll | 8626e4695db1862b13ee7398b6ceaf77edf2818b4803f23665cba484454dd6dd | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.Identity.Client.Extensions.Msal.dll | c428de0dbf5a66afb09e3f11cc932ab0096c3559456b980ec0bc0cbd2d13f64c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.Identity.Client.NativeInterop.dll | 5dcaf7095cb9a0115d39f00705643930f739d9b570eb45a3f51daedab5a369c3 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/Microsoft.IdentityModel.Abstractions.dll | 692cc596ee7a620e899335be03a83229520aed5a3e1a450c37ebff7c93dfafa0 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/msalruntime.dll | ad1b1935ccbbde75e544641bd9159e7b5bd6d394ddcf4c81aeb7cfad1ebba07a | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/pcre2-config | aafd26e63a1913d8f95ff5e2347265572fc412d0797bfab33a5c6de05c5e57e0 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/printf_gettext.exe | e3348d72114afd0ab6d1ca5c53b95dca49c91511b286a0d9bbf351d83e3683a8 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/printf_ngettext.exe | b28fe8287d440f1e1c2a2dc2c6062ad4b368ed767e80495a77536ac63f69d852 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/proxy-lookup.exe | 9a91be2b4790cf6e41da97b16b9b82aff90afb91a0f66423bfd1bb35d61c25e0 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/psl-make-dafsa | 252e22a3ad8e48542a71ae5625b3c2ca7e9b90ce5edbab68ecf4d0ccec82c604 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/psl.exe | dc02c2943d3045033c0e819c4e29c56e999fd9cabef3c5f66ef4c5d23a13b810 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/scalar.exe | a56883969932a0f194d6aa6117181db8b4f797fa1808ea01561c2137ac1c876c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/SkiaSharp.dll | 1c0fdec5e90624fbe7a5afccea355eec112ca593576fd893ee424b22304e4eeb | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Buffers.dll | 322b7e92ef79d35821f7859ce04500819e819892e80bdb4872bcc8183120b07a | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.CommandLine.dll | 7013e24a56109cb1cdf2dbe493b03540ed9cf9e23b7b35d71f37237b0c9305e8 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.ComponentModel.Annotations.dll | 46736b11724e6107112751fb20b013e9158fd9b335c19ee408b3df309b3c52b6 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Diagnostics.DiagnosticSource.dll | f539096f5e4bc3e018f00206da279a9a664b6e5a44b9c304d8949abf004205f4 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Formats.Asn1.dll | 52abac01da817aec9c53c1b4e683bcfc24ec22e86c7156a70678d3014d658c83 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.IO.FileSystem.AccessControl.dll | 03dca81b81188f83ef7621752c48417428ebb1c2e8550c3cb4c9d3aae713fb7b | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Memory.dll | a538621e978f6559c96c401a0c35f9fbbbe85c18db496c33debe93d6865d71bb | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Numerics.Vectors.dll | 0dcbc9b6f7115e8aaa401850253aef651f47615e6e2006bc99840d836a1691f5 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Runtime.CompilerServices.Unsafe.dll | cff361880bf7962e876c968bd7cc2144338e8d9dc84a0c9db933cfffc328df6c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Security.AccessControl.dll | 40d981a0cafd6c07deacc0bafb93548d282b3faadb09c5e8cb222ba77a3e7feb | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Security.Cryptography.ProtectedData.dll | 95500dff838eec1e079bc94c4e0f8db3e7df6f1fc2dfdd0a18c3276baf63e62c | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Security.Principal.Windows.dll | 0139ce79d7ec025724732f4c62e8d4008898942d18b8f040f067f7639ffd5b55 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Text.Encodings.Web.dll | 5690c9873b767956258bba077d734a92cb0514721ad6801e01e1542530ed4297 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Text.Json.dll | 76a73b925787597c25456dbe27b7bed58d2fce89034fed323f08135c20f4ea55 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.Threading.Tasks.Extensions.dll | 74f7f157ce574a131da14186964c347f6b3200cf745c67b28b52da51bf963e50 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/System.ValueTuple.dll | 420fa431a72f24995c72a57b4b134c29fd0a11e56aad1b860a1e6905d268ecb1 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/wcurl | 739a03b12f98c8ba864b8775440a5b4e337248e4986e51528da5806387894f65 | UNRESOLVED | unestablished | U1 |
| ucrt64/bin/zlib1.dll | 11cd91171765cd65f1c3362e3df67e5f5a618a6b88c8cdec899b802eaf1c7b0d | UNRESOLVED | dependency candidate | S1 |
| ucrt64/doc/git-credential-manager/LICENSE | b47f1a8a744ecdc7a3da35804f88552805d33f51a726b87a2105acdfae406b07 | UNRESOLVED | unestablished | U1 |
| ucrt64/doc/git-credential-manager/NOTICE | f573f5d21d5d8a054aad1ffcbe0165391a4d93a5aa3e23c3db0752759adfd50c | UNRESOLVED | unestablished | U1 |
| ucrt64/doc/git-credential-manager/README.md | 63c07fdc925794054be761b3fa9944f67477e68f356d2644680acb6fd789cefe | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/cert.pem | f345ac0d7dbd1a584dd80ff96eb2919e8dac68e962db2e7111401b434e888493 | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/certs/ca-bundle.crt | f345ac0d7dbd1a584dd80ff96eb2919e8dac68e962db2e7111401b434e888493 | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/certs/ca-bundle.trust.crt | 1f3e5ece4ad051bbd2a9186690df2af232e491b920e16c15eccbeebc80483e11 | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/ct_log_list.cnf | f1c1803d13d1d0b755b13b23c28bd4e20e07baf9f2b744c9337ba5866aa0ec3b | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/ct_log_list.cnf.dist | f1c1803d13d1d0b755b13b23c28bd4e20e07baf9f2b744c9337ba5866aa0ec3b | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/misc/CA.pl | 9acece758822ececa0dd9fdb553ce9fc35dec3ecd993bf00c37b6a8c049f19ab | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/misc/tsget | 81e8a07908042d47725aee30dd0770ea2f5751d6d96dce2db20596adce538875 | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/misc/tsget.pl | 81e8a07908042d47725aee30dd0770ea2f5751d6d96dce2db20596adce538875 | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/openssl.cnf | a65a2cb9f4ee8ffdc7ef4f0ac600c0bdafb95b7b1ab457188ac610a62f5ad6b3 | UNRESOLVED | unestablished | U1 |
| ucrt64/etc/ssl/openssl.cnf.dist | a65a2cb9f4ee8ffdc7ef4f0ac600c0bdafb95b7b1ab457188ac610a62f5ad6b3 | UNRESOLVED | unestablished | U1 |
| ucrt64/lib/engines-3/capi.dll | 66dbe6849c555234bb47ecf99bec422bf81ebd0f9c3aed178bbbc636b7c6fb4e | UNRESOLVED | unestablished | U1 |
| ucrt64/lib/engines-3/loader_attic.dll | 2c0cd193a259175def7d5c58903f460248b2592d15d83de2796c0edb77c0cdc0 | UNRESOLVED | unestablished | U1 |
| ucrt64/lib/engines-3/padlock.dll | 19e01a9409eda58c2dc1835d79fc452ba5f7e737164d5affbe8e04abb80d14d2 | UNRESOLVED | unestablished | U1 |
| ucrt64/lib/ossl-modules/legacy.dll | 946401e9abe73c09f6ff80922f508890e2a06129e19b257064c6f0efdb381746 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-credential-wincred.exe | 1cfe1f08b67aff48f6f033c4afc909e5658e39c0cfd4c4a9f7741031ab875459 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-difftool--helper | eafba74e4934494c0017f8b06375b3c7e67c84ac285b8492976c51de2f7da619 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-filter-branch | 62285b171fa3f70ece4eb5b8283f60a4d112b65f0cb6b9e593b1f16b93248282 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-merge-octopus | c5d08a8c4e5afc8b48d965c309d3b98930592da304cf04ac265c8b24ea3d6891 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-merge-one-file | 496bd3daaca988726b23252e8032f8e3cc38913dbe2a0d9f1bafd7b7276ae717 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-merge-resolve | 5638e11ae0ffa26607545afc060cc603083863acb1f7c723547d6dc1d3ff29c9 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-mergetool | 445d33f9aa9e1f93afda20fab277904599151af08463316ad45ff0a650031d10 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-mergetool--lib | 3fd517e10d0cd0febd5bdda9c7ba2189646fb2747345cd8d0bc5ddea4c42f05c | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-quiltimport | a103092c9c97d3b202477ae1391ea56b3c30ad40a2cef152dca6980fb5e57fa4 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-request-pull | 679c05f4a1fde059dc14e583deb3b63f4ba3f79697c08bb69af2b6130c0bd104 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-sh-i18n | ea7006272625aea626c48e216c6361d3b50c794b01c361fbe1cfe5a7f7bafde2 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-sh-setup | a79e1ad765c27e18f0356a5dd97383ba03e0efd33ccba8c8122f45f37eb78fa2 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-submodule | 55a1a450b48fb98cc8c3f5745c411e3391ac7659f46eb4b7eef9053aa3614353 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-subtree | 444416f46ec74b1c5cfed1df07ce89fe32f17b368950c86780079ded3a3577ae | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-update | 15b40ab72dea884f659cfbe441e9a40b2d8d63e490a3c14824a55607368e476d | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/git-web--browse | 5c0d1d91dadfba3fe353add1f07be76016a7c6a3b2260ff9dfec5491fcd9e5e6 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/araxis | 49aa2286e6ec2d7c0fb4077a2f9c5a757537476c07f517694fcc79dca021aa31 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/bc | e54e6e1b38bbcd7ededcad7d6e05638453dd4c10631e392ecebfae8d396b01b6 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/codecompare | 7ee88c614edf10653d6c66f94a6f19a469551cd21aab224ad97101661cda0dc2 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/deltawalker | 4c64c36c09ba536fc5bd822be2750f6f6dd74b5c2feffc5564b5d51d55f120c1 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/diffmerge | d1b72ad340d905e6ea652069b870fcac2cbfa5296e13b35701d99d3cabc7bfbf | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/diffuse | ba5c97c501cae4219a7f4db36ea3934dbde0768a06818b1d49acc63070acbdaf | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/ecmerge | 2d23869a9a5c52a45d1d76fff9b446a77fd2205a1db63090fa072ea3e12d5fa6 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/emerge | 014c19e4a9c4227cc08b53703ada35283882ecabada96198ca98c7238cfc9135 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/examdiff | 162a10db12c2574d424172fdf00c1b097e0c1be900458da27d4619a9005d281d | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/guiffy | 294fd58816e5105234628d99af3c64bcc105826171da32ea8134649d9592613b | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/gvimdiff | bc1d96063154a0e5a7f55f5f3579d275c124e84ba33eb50db2f5802e259b479f | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/kdiff3 | b5c69d346db89853a21287b3b2b9f0f923123b691e9f0ebeb0422125fdd8a5ac | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/kompare | 1e57841ff2f88c6d66cb979b43f382a3e476a747825c1abd32a95f0c26e64b6f | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/meld | 8913bd55b2ab6afd4b9776b18cc7b409e134beeb3dd63aa05d21b53fe027312b | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/nvimdiff | bc1d96063154a0e5a7f55f5f3579d275c124e84ba33eb50db2f5802e259b479f | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/opendiff | b43bb602aff994bc92f007d72398cb1439bfaa8d5eb5df3cc99f9e6aaec73901 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/p4merge | 4d1f6e3cdd1a06d600c672ee4ca88d83b50b8cf42c4f7be0fac323b5c4b32993 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/smerge | a40d6cae6fa097464595c94ffcca127672b7838d21c5b47efad880fd6afe04f5 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/tkdiff | f1c788423c7a7792319168ce5c5c871918b7f6f428c7304e511692702bf260d9 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/tortoisemerge | 6d0a7e1f66eb108327816949b6cbaef0c727d05fc77c60870a2555b401a93c5b | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/vimdiff | 07fa80716e5e8a4b0449a8ff471d0221c34265b9ee80d939bbd7e1a2744f7bd1 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/vscode | 58677f9c457844c3138fa66905a54a9670954ff9721c1f03c229176b7feaafe1 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/winmerge | 18e584efa573fef5a04d5701fa237f83dfa5fb058b790c6aaff27eba33835f07 | UNRESOLVED | unestablished | U1 |
| ucrt64/libexec/git-core/mergetools/xxdiff | 9184e4eab6bb40f09834f27dca31244e8f9028047a97d07467d9c340abb82a87 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/bash-completion/completions/git | 3b1018983d1ca279967403e65d1dac8b4afd30baafdf104f057a652c199015a6 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/expat/AUTHORS | 59f14371c6b75912cfebb46e6247ee5146766e803a0365b124e5d3011e7d0877 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/expat/changelog | d524be92cf55121cb6cb7bc13625f0498f1d31b4990fb52c93a574edbb372939 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/git-bash.adoc | c975292adae1f2666f07f8ee9b7d50576da249d9151c6bd211602adc8d37b6ab | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/git-bash.html | b20fee313156af402656620b99b73543d457c26feda92088f0091ed602255dd4 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/git-credential-manager.html | 0495bb591a5b5ef14743bc68be7ad513d508ffb4d4a96277b5918c172aabd484 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/git-send-email.adoc | f7de0cce8f858e741b4bd38cf6e3ff394a44f246e1347fbf1bd64a06f5517863 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/git-send-email.html | a943d8b5b26e1f824f4ddf8e1e2c650a6d5a7cb0ee330ed624183561086916eb | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/git-subtree.html | e1cf55a443c2ed24056977d6a61c19e2f19a6bd6ce3a843707d2f04181a63978 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/gitk.adoc | 7f8e2cbdfe1d74bfbfd546fee4f9ec8b96afcf3f3edc42106c18eab67633fa78 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/doc/git-doc/gitk.html | 1f6d8c764a50502e39141e626c50c33e02bb434ddb05941aa3ef6a6a8664b9ef | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git/edit-git-bash.exe | ddd477d1bfbc379bdf609e92572099880e80deb99fba2507fba6727cd378c741 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git/git-wrapper.exe | 9af8b86cb229e389829f579136c0baad689aba575e332b05731dd6efabe27a1b | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/description | 85ab6c163d43a17ea9cf7788308bca1466f1b0a8d1cc92e26e9bf63da4062aee | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/applypatch-msg.sample | 0223497a0b8b033aa58a3a521b8629869386cf7ab0e2f101963d328aa62193f7 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/commit-msg.sample | efc1401b0e99d1ff51494d154d98b46c1e99059bcd8bf9f73cecde19fd3eb23b | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/fsmonitor-watchman.sample | 9159720099ad5595b8e66645cbfd47763c1e920f46e0b50ae75e642bbec57ef0 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/post-update.sample | 81765af2daef323061dcbc5e61fc16481cb74b3bac9ad8a174b186523586f6c5 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/pre-applypatch.sample | e15c5b469ea3e0a695bea6f2c82bcf8e62821074939ddd85b77e0007ff165475 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/pre-commit.sample | 57185b7b9f05239d7ab52db045f5b89eb31348d7b2177eab214f5eb872e1971b | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/pre-merge-commit.sample | d3825a70337940ebbd0a5c072984e13245920cdf8898bd225c8d27a6dfc9cb53 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/pre-push.sample | ecce9c7e04d3f5dd9d8ada81753dd1d549a9634b26770042b58dda00217d086a | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/pre-rebase.sample | 4febce867790052338076f4e66cc47efb14879d18097d1d61c8261859eaaa7b3 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/pre-receive.sample | a4c3d2b9c7bb3fd8d1441c31bd4ee71a595d66b44fcf49ddb310252320169989 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/prepare-commit-msg.sample | e9ddcaa4189fddd25ed97fc8c789eca7b6ca16390b2392ae3276f0c8e1aa4619 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/push-to-checkout.sample | a53d0741798b287c6dd7afa64aee473f305e65d3f49463bb9d7408ec3b12bf5f | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/sendemail-validate.sample | 44ebfc923dc5466bc009602f0ecf067b9c65459abfe8868ddc49b78e6ced7a92 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/hooks/update.sample | 8d5f2fa83e103cf08b57eaa67521df9194f45cbdbcb37da52ad586097a14d106 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/git-core/templates/info/exclude | 6671fe83b7a07c8932ee89164d1f2793b2318058eb8b98dc5c06ee0a5a3b0ec1 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/brotli/LICENSE | 3d180008e36922a4e8daec11c34c7af264fed5962d07924aea928c38e8663c94 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/curl/LICENSE | 82f2f4427d6545ee5aaac4f0b80428da6cc8ba41c2cf5da3a03680ec327b9681 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/docx2txt-rs/COPYING | 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/expat/COPYING | 31b15de82aa19a845156169a17a5488bf597e561b2c318d159ed583139b25e87 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/gettext-runtime/COPYING | 7ef2cdfe58e0c0460657b6598b49af29d4e03c1e41cbaf0e1da1eb8ad74b95d0 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/gettext-runtime/intl/COPYING.LIB | 20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/gettext-runtime/libasprintf/COPYING | 03133addae5b99a6148c538300e6d97074453089be1423b741bd081f18e2b298 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/gettext-runtime/libasprintf/COPYING.LIB | 20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libatomic/COPYING.RUNTIME | 9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libatomic/COPYING3 | 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libffi/LICENSE | 17b64dc60f3b6897a60f971e288b973f655c2edcdf08b25f3c3dd5549857881c | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libgcc/COPYING.RUNTIME | 9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libgcc/COPYING3 | 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libgomp/COPYING.RUNTIME | 9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libgomp/COPYING3 | 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libiconv/COPYING | 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libiconv/COPYING.LIB | 20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libiconv/libcharset/COPYING.LIB | 20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libiconv/README | 4ae66e61d1c6593c84c47105b368d579bcee1af566dbb959ec63a0c48425dcf4 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libpsl/COPYING | 322392e6001b2b3b0fca705dc9f11f26e12441188ecde50eb1d22909980b2925 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libquadmath/COPYING.LIB | 32434afcc8666ba060e111d715bfdb6c2d5dd8a35fa4d3ab8ad67d8f850d2f2b | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libssh2/LICENSE | f7f9633cf9ff2f1333f3d7ce46973a8716a4d2a2815ad56f30d437d5fea7bafe | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libstdc++/COPYING.RUNTIME | 9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libstdc++/COPYING3 | 8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libtasn1/COPYING | 3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libtasn1/COPYING.LESSERv2 | 20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libunistring/LICENSE | 3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libunistring/LICENSE.LIB | a853c2ffec17057872340eee242ae4d96cbf2b520ae27d903e1b2fef1a5f9d1c | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/libwinpthread/COPYING | 63263614cdd29f2f93cba85e992f041b31f9fc7b4033692f31269489a8a1b177 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/nghttp2/COPYING | 6b94f3abc1aabd0c72a7c7d92a77f79dda7c8a0cb3df839a97890b4116a2de2a | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/openssl/LICENSE | 7d5450cb2d142651b8afa315b5f238efc805dad827d91ba367d8516bc9d49e7a | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/pcre2/COPYING | 99272c55f3dcfa07a8a7e15a5c1a33096e4727de74241d65fa049fccfdd59507 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/pcre2/LICENCE.md | 197d8a73ffee0d6b09adba2f9c677b5f5aede24edf89258a68e48248d010d811 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/zlib/LICENSE | e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2 | UNRESOLVED | unestablished | U1 |
| ucrt64/share/licenses/zstd/LICENSE | 7055266497633c9025b777c78eb7235af13922117480ed5c674677adc381c9d8 | UNRESOLVED | unestablished | U1 |
| usr/bin/awk.exe | f123d2c120b2ad2158aa8c69d8eeedf14c0d681e68ee76ff103e06ac49986200 | UNRESOLVED | unestablished | U1 |
| usr/bin/b2sum.exe | 604deb03fc039e3588a782010774a9d7b4f785f015323a4f4739ac26070569a4 | UNRESOLVED | unestablished | U1 |
| usr/bin/basename.exe | 6fe2e201a956304503f808d0909a26d9b49e1a7e99f6ee6d93721ac4a76a7c6e | UNRESOLVED | unestablished | U1 |
| usr/bin/basenc.exe | 39a435a6a46a997417630bbc5374e89f3d34673eb10e65cee6122a6bb547d47e | UNRESOLVED | unestablished | U1 |
| usr/bin/cat.exe | f1b37048ee5c70fdc31dde509e562261c9b2d102d94c903393f55b45e883ef90 | UNRESOLVED | unestablished | U1 |
| usr/bin/chattr.exe | 23d80c2dfe495b90252a67a60a4f511bad01433ae276756479681feb2ada3d61 | UNRESOLVED | unestablished | U1 |
| usr/bin/cmp.exe | 9436e2a0a92e8f31e02077785f075fb62d05074d4ce257c53434b93497b0eb2d | UNRESOLVED | unestablished | U1 |
| usr/bin/comm.exe | 7b1a630adb1d85b4f3dd8247a45a914ead7bc34e8b72b8c4a1f12baa82aa80f4 | UNRESOLVED | unestablished | U1 |
| usr/bin/cp.exe | 5f91e0b445edb4e4c17e9a660ac29239f6cac5a821a173a86d4332b9eaa8cea3 | UNRESOLVED | unestablished | U1 |
| usr/bin/cut.exe | 63fcfb76c80d57538312a9637429d5a4b99ac83e8b00d95684609b4c045471e9 | UNRESOLVED | unestablished | U1 |
| usr/bin/cygwin-console-helper.exe | e33cfbf8a8876fe32915f880714f5bd92acaaf7b0e8fcd1340598ae3c26a6158 | UNRESOLVED | unestablished | U1 |
| usr/bin/dash.exe | 61dc29be7b19d8f5facffbf0c1b6df7d40f064743f9902d2e51d51f4409f762d | UNRESOLVED | unestablished | U1 |
| usr/bin/date.exe | 743228ae082e1128a2aff02414e114dc45a51f7461775bc5750d89307f3ccdac | UNRESOLVED | unestablished | U1 |
| usr/bin/diff.exe | d64621f766d8910a92cb3d99bd7f23c0b1c736eece0e19dccbccead93aa81854 | UNRESOLVED | unestablished | U1 |
| usr/bin/diff3.exe | 913e23ff6b2f9dc204b92a181ac993e3ce7c8c5bcd68db3f7662224a1896a975 | UNRESOLVED | unestablished | U1 |
| usr/bin/dirname.exe | 53896fda354605a1a1d1f5e6802daba5ba6c05961f3074b892194e068aa82772 | UNRESOLVED | unestablished | U1 |
| usr/bin/echo.exe | 629697ea64fad72bceda3b2a6fe3c60c79e1a55e0a79de54f04ddf840907cf41 | UNRESOLVED | unestablished | U1 |
| usr/bin/env.exe | b5d80f13e6b4b422a8c22d32be9cc1f5fd9b482fc60008ed80e513a2fa938cdc | UNRESOLVED | unestablished | U1 |
| usr/bin/expr.exe | e1608f26781374b67f180370dc50c833bfc61946aadfb433e48536590bb79219 | UNRESOLVED | unestablished | U1 |
| usr/bin/false.exe | 71314347cf1355d1fd818d62fe11cf6b58373e70170a273335d38a8bacb987d6 | UNRESOLVED | unestablished | U1 |
| usr/bin/find.exe | 1729ceebf52cf72bf1fc955af8167f2ba8ecbffa928fa386818affc5a60224fd | UNRESOLVED | unestablished | U1 |
| usr/bin/gawkbug | 475610aefc76b89592ae8440434368bd448f7c7391146d91b13758f65120117b | UNRESOLVED | unestablished | U1 |
| usr/bin/gencat.exe | 34ac90b2ae45ab95bde26a8a485ec7404c281cabc54d82575ab86b6ed32cafde | UNRESOLVED | unestablished | U1 |
| usr/bin/getfacl.exe | 790b8138ca26f52b7de61cdb857e4d160a65853c3b5f3dd115468db0a643eb66 | UNRESOLVED | unestablished | U1 |
| usr/bin/getopt.exe | 9ab321a755847a5cb427246ef063b2b6cd74673ff866a0836f6d56b90f8fe41f | UNRESOLVED | unestablished | U1 |
| usr/bin/gmondump.exe | 8e9e44ea15fa2dc8327179960e5e1dd66ed951523cab823867a999c46c9b675b | UNRESOLVED | unestablished | U1 |
| usr/bin/grep.exe | 497202418334f8a48d9f34cd2e1b2c03c4f957e02304b613e10931c0457e8d4a | UNRESOLVED | unestablished | U1 |
| usr/bin/head.exe | c82ae2ef72235a34db7007580628cd5183cb350878a10fcc98b6ef26b92a3537 | UNRESOLVED | unestablished | U1 |
| usr/bin/ls.exe | b45981580702029cfeeffc8ca69e2a4d1e9c68914009e94c31ffec9cbc544aa5 | UNRESOLVED | unestablished | U1 |
| usr/bin/lsattr.exe | 69733aae0376de6fb36bd064598afdcea547e2bbeecaa348d1998beb5d336d7a | UNRESOLVED | unestablished | U1 |
| usr/bin/mkdir.exe | fc9b9e49fd6496cdddfc5681208d74bd649ac934818eafdfd50a9571bdcb4861 | UNRESOLVED | unestablished | U1 |
| usr/bin/mktemp.exe | bd6474b0404e52b195296438342f38e510fe1a4c1c0d91ceb83cf8411959fecb | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-2.0.dll | 2a89b7c31b323c42e2fb37900af087aeb27417694e630a210bc75b0369410bc7 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-asn1-8.dll | 24e7a09a283ee7562c1889b5319269d838cddcab837cf3df7356b0a60bff2efb | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-cbor-0.11.dll | 6b27ae38e5a01d9b60f0e40753b158043dcf1258c29bc700b97b6eeb081b41a6 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-com_err-1.dll | 541eec990f72219d49033b49a9c394610f0c98feb05ff3e94d965e1be5830e8f | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-crypt-2.dll | 9a06bdbd7a934847bc0c50c3a19a7cf2b036a86ef9960fbe22984dd2ac18d608 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-crypto-3.dll | aab8ecfcd2cc741057df33f97438bcefc5626e7cde8a20b6db27e996d478f9e4 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-fido2-1.dll | fe428e64b696420ca7b508674d5a92dc9f89fea81197b0653f966b57a2162a1e | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-gcc_s-seh-1.dll | 59b816ee2880c2140ac8d7726f59e4e7435e309f272a80fd590d3130215f77f5 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-gmp-10.dll | e3d88ffc1bd3bb3bdda1d84f3f823e6f0f07c89dfd17e2d003c588f56dd80784 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-gssapi-3.dll | 483a33bb29bc4decbcecb5298d1da6d134814abfea985501571bfc492fc66ac9 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-hcrypto-4.dll | 542bb844e0af85188e55645a53cd6c9ff33d8757214a23e7fa6cb73047f48678 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-heimbase-1.dll | 0cb52850d34714d1b3d13b4ae8b9ecab54be73e2a7b00f2c45a13827bf0a5c6a | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-heimntlm-0.dll | 5abb16fff85e9054ba552d225f6d370c5d806bb6498e6b96e7c4797c55791312 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-hx509-5.dll | b3b7210e5e2f00125357fa2e377406ae220a3527a8051a28f0fcc761f83e2da0 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-iconv-2.dll | 50012969ed96a5232220185d2fc1ac1e3abe5790f6b3027f4fc3c4cad3fd38f0 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-intl-8.dll | 50f7de0c712d867ddca2c9eb8562ca6ee2d69e120e798ec6126ad29dd1ed5402 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-krb5-26.dll | 1aa90c10f2f31101faeb356bf4112892b5bb983aa62d30b51b2a508cce32c1ff | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-mpfr-6.dll | 7be008ed823d8ce65a205669c44fd8ad56eee5838111101d29c6684f8eccc4f4 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-ncursesw6.dll | aef26ffbcd20ee5781c3a5e81265390494090e13561a13336d000d9d5f9a84cb | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-pcre-1.dll | a94b1a5ba095ac7ff81e138a1231e42e3a07391e85eeb86c3bb5c9245244597a | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-readline8.dll | 0c7c38f1b76e087add0faca414659c3d25008a893dd4b185604a4183bb68132b | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-roken-18.dll | 43cd75f19c90c4383f43ef19a2721db5521c27b6daa5909c66e54d39354e7314 | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-sqlite3-0.dll | fad59b1dda3ccf29fbb57b3656b6fcd95feda095735e17445b41d95c2c0aaddb | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-wind-0.dll | 4e516c0d25ee1f01e48afb81081e0d7f7078358628e135b33ef822485eb357ca | UNRESOLVED | unestablished | U1 |
| usr/bin/msys-z.dll | f548bb1632160282c3853415182d695c655d0eb7c12aa42a0538161898694b6f | UNRESOLVED | unestablished | U1 |
| usr/bin/mv.exe | 0e990f9314e17eaf2eed168561313e0b6e1d21daf8fb6400387026c6da7277a1 | UNRESOLVED | unestablished | U1 |
| usr/bin/newgrp.exe | 396913ff51486b761d05eb7091059dcf4250655bd72c0434ec377b4ad546c809 | UNRESOLVED | unestablished | U1 |
| usr/bin/pathchk.exe | 36afccc7251e0b1a5b2a7c54fe022d13a122c2479028b0f01e653084e79281e9 | UNRESOLVED | unestablished | U1 |
| usr/bin/printf.exe | dbc52ee41a9d2fc4cdad6d690e430c6b630ce5fb5837d66d6b47cf59ea63b198 | UNRESOLVED | unestablished | U1 |
| usr/bin/profiler.exe | 5da5ee30b0c9ac6fffb856ea2bce5af1854c6a81b6129a12f157b242c67b711f | UNRESOLVED | unestablished | U1 |
| usr/bin/pwd.exe | d1281cecce65fc76750381698faca130216ffacc6396886d63a85ad28a3071aa | UNRESOLVED | unestablished | U1 |
| usr/bin/readlink.exe | 3617334c256348026305e7a978bb803c45c31e2f4d24c763e1f11361ceb1d58c | UNRESOLVED | unestablished | U1 |
| usr/bin/rebase.exe | eccc5d1189f6ae079b461bee498e784c7f1516a7aaae08acc8306c669675dee6 | UNRESOLVED | unestablished | U1 |
| usr/bin/rebaseall | 4fb45b485ca2215abf5fcda5bc46d0a59ba6edb25ec327680e8fd142469311a1 | UNRESOLVED | unestablished | U1 |
| usr/bin/rm.exe | a845f7517a49b49726e056da8a8f65a6d9ce96fbe79c3664c082521eea0f80e7 | UNRESOLVED | unestablished | U1 |
| usr/bin/rmdir.exe | 7d91cc7b4e7a297a74dcdb621ff19b495db14a8a96612a737fc870403fc6775c | UNRESOLVED | unestablished | U1 |
| usr/bin/sdiff.exe | 1ebf31bdfe552d728c940866ffb0753a745e9699b69c79013d8766242d6714a6 | UNRESOLVED | unestablished | U1 |
| usr/bin/sed.exe | 8d54e322dfc3faa60f0464691aba8634197406e53367aa8942409181c0808be8 | UNRESOLVED | unestablished | U1 |
| usr/bin/sh.exe | 5490d0da5e7cf9d92068cc48fcc590f2bcf8564add8ff91c3b5fe541eb2d72e3 | UNRESOLVED | unestablished | U1 |
| usr/bin/sort.exe | 7c5df851d821e23988641f35442a06652ce834ed724456511798ce60314cab9a | UNRESOLVED | unestablished | U1 |
| usr/bin/ssh-add.exe | 5da94050af77068cbafdc5d204af47f57a050c38c32cdbc3d4644de9b8e211ee | UNRESOLVED | unestablished | U1 |
| usr/bin/ssh-agent.exe | b2cf721b47eea0bd55ba58ed14f30049fee2b58f89c1b238415bd6960c088443 | UNRESOLVED | unestablished | U1 |
| usr/bin/ssh.exe | c84594a323ee6afc04d9faf614a05be6dc9a2faecd856268a854084fea17fd44 | UNRESOLVED | unestablished | U1 |
| usr/bin/tail.exe | 8608c4138642de6dca0806b266b3009c137dc373171978cf47418056a5e05c55 | UNRESOLVED | unestablished | U1 |
| usr/bin/test.exe | bc151f331dbbe8d8558014bc55b983d20effd4ebbea04d2a29b6badf879ce423 | UNRESOLVED | unestablished | U1 |
| usr/bin/touch.exe | 1d895e0f77cbc8b77c3a38da009e8ad8d23a371afd398da5408bdeffcddf5fc0 | UNRESOLVED | unestablished | U1 |
| usr/bin/tr.exe | 7cf90be63820ba9ec66a10c0c4af84f0a2e3ec90a722ea6904219ec0b93bf1c1 | UNRESOLVED | unestablished | U1 |
| usr/bin/true.exe | e3ce235425032cc3e1262f46b414b1b88f971724104916690f24e25c4663d474 | UNRESOLVED | unestablished | U1 |
| usr/bin/uname.exe | 1cba275ff8e0c81f48898f017758c558ee5951cb0448c36628580beffdf4ef89 | UNRESOLVED | unestablished | U1 |
| usr/bin/uniq.exe | 07e78095a79870b52ac988989faa5ff8446e1a8cdc861165d7eb93904fff5211 | UNRESOLVED | unestablished | U1 |
| usr/bin/wc.exe | 3ab05efc4703295f0d36fd48da17f2021219494fb932a062a535ae17ea9f45b3 | UNRESOLVED | unestablished | U1 |
| usr/bin/xargs.exe | 14097e707f43f2c1e4b60a72a02e1e7a950faddc48b7cbe81b6a2ee037811fa0 | UNRESOLVED | unestablished | U1 |
| usr/etc/profile.d/gawk.csh | 9ba2af9853121df6dd5edff9254a2946e39eab8dc6513348fea28f739ee96648 | UNRESOLVED | unestablished | U1 |
| usr/etc/profile.d/gawk.sh | 70621a3b586d3d523b020e76977633b444a70013ba50e1ea901a3a07a676f15f | UNRESOLVED | unestablished | U1 |
| usr/lib/ssh/ssh-keysign.exe | b0c586acfe1fdd0596de5139fc39165d27c966ea3c23aaaa1ae3515f605ba7fa | UNRESOLVED | unestablished | U1 |
| usr/lib/ssh/ssh-pkcs11-helper.exe | 9e3bfb621d46c55e643ae354200187f42885bf3341571ee00d3096ec15d3a3c0 | UNRESOLVED | unestablished | U1 |
| usr/lib/ssh/ssh-sk-helper.exe | 5e32e4f6e94b5975417a7d2e1794dbf18c5beaf7e453b719edc80ff067ed0737 | UNRESOLVED | unestablished | U1 |
| usr/libexec/getprocaddr32.exe | db0dc45b5711b7835f3a04e851f15240b22222e2b1cbfa6b193b55e5ac738e70 | UNRESOLVED | unestablished | U1 |
| usr/libexec/getprocaddr64.exe | fae7db029ce888c1d1b4c452ef9b3fdf780e2372916ec74d2c06734a412f3f9b | UNRESOLVED | unestablished | U1 |
| usr/share/awk/assert.awk | 6c4b3f24dd0c225f3ece786eee7fa75f4ef2fb7ffedddaacbc2edb03c68c90b9 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/bits2str.awk | 77c2504aa2d6385d4d3c0d350515b8791070060ace1414bccc6dc99153743237 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/cliff_rand.awk | c405417ad13fe4ca0ba783b6fdcf90c1e2a8ae80ffebc0f2107ddd6ac22ecd82 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/ctime.awk | 2e20e707381b7cd48abdd70e8f7aed8d86db28a35193bf296964e82de3b754f8 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/ftrans.awk | 11b367afeda7cc11b3f829d931965ea56b10fcfe87b3833ac4a9ccfce5830ee1 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/getopt.awk | 7394647d52ed67c12097db732a96f25c808e5d432d74a8c3f0724602f7d41bb6 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/gettime.awk | bc0fe06e7fb41531748177f255a20c0db6732472851154b0370532fc302c1864 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/group.awk | 5ac6963d2e520c9f76b783b527a2bb69919bc742bc73ee6aab55866e70bd129c | UNRESOLVED | unestablished | U1 |
| usr/share/awk/have_mpfr.awk | a017c0ef4b5311bd94228c366a896a4a5af417c41930f7ea2b46d9d67f2a663b | UNRESOLVED | unestablished | U1 |
| usr/share/awk/inplace.awk | c74afe20269e7747b55211dd48bef10fb1b9177dbd2997905ba261f2f4fe1243 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/intdiv0.awk | 26b599f90636b540d77e36724f7339c1330307cf2fafe32d00e7977764bc87ad | UNRESOLVED | unestablished | U1 |
| usr/share/awk/isnumeric.awk | 8749b7f590a8997387fbb1cb7317352f05089778d8223b03b8a7891f4c55dfed | UNRESOLVED | unestablished | U1 |
| usr/share/awk/join.awk | 49de451cda05448408cb6e5210eb7d886dea05f182e57edd1ecd65afabee8a66 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/libintl.awk | 293d54512ccf8b6eb41c3f0c9e7ae6d1a20b1c9e7eb559d4975de45ba478f6e1 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/noassign.awk | 63a84996567a8be236bb4955ee55d525387d0513b12e2121e92267ad72a9c20d | UNRESOLVED | unestablished | U1 |
| usr/share/awk/ns_passwd.awk | 6d4b76c1cb895dd7cdae0f1e9e34f474003486e653693684784d0bbcbb18389b | UNRESOLVED | unestablished | U1 |
| usr/share/awk/ord.awk | 23bf677aa27bed203790002eeade4996910505445d560ac330236a11b63884e8 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/passwd.awk | 4eb7cac4bc00262710085f95882cc26f23db634dd23a9a5811ba2dfcf17b1bf0 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/processarray.awk | 8aba77f62a7d63ee84717fa019175bb3f389406f8266188aaaaa0544d08ba302 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/quicksort.awk | c04bc6a885680793fc06a9fb3c0d57903c36383ecf3a5b1c5b05d137b141d7e7 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/readable.awk | dfb704d2168f9a1742c4f662c8ae3d17cee8844829fd92249bff79c5f5152942 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/readfile.awk | d7c4f63b17c19b2a769ed0c0cd80c94d594e7c413d774ddf629e7464b06f961d | UNRESOLVED | unestablished | U1 |
| usr/share/awk/rewind.awk | 6b16e49c6a1e99da1d3c05f5ea9b9128a130002f5c67e1f94e81e6e697b15a61 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/round.awk | 024ed109f713670ddfa752de0379019f95d6b10cd774a181943f2cf0ea024f80 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/shellquote.awk | 2efde58fd4fca1f0b27eeec6c04fb7869f9abb1ddaf2f776ec9553ca18b2728e | UNRESOLVED | unestablished | U1 |
| usr/share/awk/strtonum.awk | 4af52a0653670b997a3365713bbed43737a07cd6b5064434e863484a0a074122 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/tocsv.awk | 022016e528bae702238cfc65a6a466cb3ac4883ea7f542a9dbcf8530776761d8 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/walkarray.awk | 90a9543fa6e49afb453a41e00dce7353d44e2c189ec7cc1c640585bcf1398c54 | UNRESOLVED | unestablished | U1 |
| usr/share/awk/zerofile.awk | 2aaae54a27113af872b61cd969196be9d21a309cac9d5307a1db3b33530eda86 | UNRESOLVED | unestablished | U1 |
| usr/share/licenses/gcc-libs/RUNTIME.LIBRARY.EXCEPTION | 9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74 | UNRESOLVED | unestablished | U1 |
| usr/share/licenses/libopenssl/LICENSE.txt | 7d5450cb2d142651b8afa315b5f238efc805dad827d91ba367d8516bc9d49e7a | UNRESOLVED | unestablished | U1 |
| usr/share/licenses/libsqlite/LICENSE | 0b76663a90e034f3d7f2af5bfada4cedec5ebc275361899eccc5c18e6f01ff1f | UNRESOLVED | unestablished | U1 |
| usr/share/licenses/ncurses/LICENSE | 708999f95527e1ffa670c6fce288c6c600cb477dd04afcc1171422b3dd4ee226 | UNRESOLVED | unestablished | U1 |
| usr/share/licenses/openssh/LICENCE | 5bb5b160726ef5756e4f32fe95b35249c294962419650f48d05134b486d27ccb | UNRESOLVED | unestablished | U1 |
| usr/share/licenses/zlib/LICENSE | e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2 | UNRESOLVED | unestablished | U1 |
| usr/share/nano/git.nanorc | 17c90698d4dd52dd9f383e72aee54ecea0f62520baf56722de5c83285507c0d9 | UNRESOLVED | unestablished | U1 |
| usr/ssl/ct_log_list.cnf | f1c1803d13d1d0b755b13b23c28bd4e20e07baf9f2b744c9337ba5866aa0ec3b | UNRESOLVED | unestablished | U1 |
| usr/ssl/ct_log_list.cnf.dist | f1c1803d13d1d0b755b13b23c28bd4e20e07baf9f2b744c9337ba5866aa0ec3b | UNRESOLVED | unestablished | U1 |
| usr/ssl/openssl.cnf | e4c87d84d4650c39a0163544a4107842b2ca42487cb61ba570b03b011275d6c3 | UNRESOLVED | unestablished | U1 |
| usr/ssl/openssl.cnf.dist | e4c87d84d4650c39a0163544a4107842b2ca42487cb61ba570b03b011275d6c3 | UNRESOLVED | unestablished | U1 |

## Distribution structure observations

The inventory includes ucrt64/bin, usr/bin, Git helper/scripts under ucrt64/libexec/git-core, Git templates, system/configuration locations, OpenSSL resources/modules, credential-manager managed assemblies/resources, and documentation/license trees. Those package locations identify plausible investigation groups, not definitive dependency/other roles.
A bounded Git command profile has not been supplied for this classification scope. A file unused by one command can participate through another operation, configuration setting, transport, hook, helper, or dynamically selected loader route. This report neither excludes nor proves those routes.

## Outstanding questions

1. Define the exact proposed Git command profile, repository/config inputs, allowed transports/helpers/hooks and environment before exclusion decisions.
2. Establish accepted loader/search rules and actual resolution of the four static import names; do not convert basename uniqueness into loader verification.
3. Resolve system/API-set imports and distinguish the declared host trust base from packaged operational dependencies.
4. Determine operation-specific dynamic loads, executable helpers, scripts, credential components, configuration, CA bundles, OpenSSL engines/providers and managed runtime surfaces.
5. Establish why any proposed other member is non-participating under the exact profile; lack of native import reach is insufficient.
6. Define how static evidence and retained measurements bind to the eventual execution tree. ZIP digest ratification is not extracted-image identity or operational pin ratification.

## Next minimum scope (not executed)

A separate documentation-only EB-1 follow-up can define the exact intended Git operation/config/environment profile and an evidence checklist for the four static dependency candidates and representative helper/config/resource groups. It must keep unproven classifications UNRESOLVED. Further static file-content inspection requires a named scope; no live Git execution, binding evaluation, runtime pin ratification or privileged test is included.
A real execution-binding or operational-pin stage requires separate explicit Human authorization and an approved evidence/measurement method. N2 issuer/verifier/nonce-holder/clock responsibilities remain outside this classification scope.

## Preserved boundaries

Existing inventory, ZIP, Human Finals, Design Freeze, PINs, distribution digest and code were not changed. No Git command, Git binary, evaluate_execution_binding, ratification, commit, merge, push, download, installation or external event was performed.
Execution binding real: UNEXECUTED.
Operational MinGit pin: UNRATIFIED.
Filesystem/reparse/loader/ACL/process isolation: UNVERIFIED.
Dependency closure: UNPROVEN.
Freshness: UNPROVEN.
Independent Witness: NOT_CLAIMED.
FULL_INR_READY: NO.

