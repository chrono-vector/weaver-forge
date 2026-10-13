# Weaver Forge: compile-only static ABI checks, no .cmd wrapper, no linker, no native test executable.
$ErrorActionPreference = 'Stop'
$Cl = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64\cl.exe'
$VcInclude = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717\include'
$Sdk = 'C:\ABI-Verification\SDK-10.0.28000.2705\c\Include\10.0.28000.0'
$Output = Join-Path ([Environment]::GetFolderPath('Desktop')) 'WEAVER_FORGE_ABI_STATIC_ONLY_RESULT.txt'
$Temp = $null
$Log = New-Object 'System.Collections.Generic.List[string]'
function Note([string]$Line) { $script:Log.Add($Line); Write-Output $Line }
try {
  Note 'MODE=COMPILE_ONLY_ABI; NATIVE_CALLS=NO; LINK=NO; CONTROLLER_ABI_PIN=NOT_RATIFIED'
  $Includes = @($VcInclude, (Join-Path $Sdk 'um'), (Join-Path $Sdk 'shared'), (Join-Path $Sdk 'ucrt'))
  foreach ($p in @($Cl, $VcInclude, (Join-Path $Sdk 'um\Windows.h'), (Join-Path $Sdk 'shared'), (Join-Path $Sdk 'ucrt'))) {
    if (-not (Test-Path -LiteralPath $p)) { throw "PREFLIGHT_MISSING=$p" }
  }
  Note "COMPILER=$Cl"
  Note "SDK_INCLUDE_ROOT=$Sdk"
  Note 'CMD_WRAPPER=NONE'
  $Temp = Join-Path ([IO.Path]::GetTempPath()) ('wf-abi-static-' + [Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $Temp | Out-Null
  $Src = Join-Path $Temp 'abi_static.cpp'
  @'
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00
#define NTDDI_VERSION 0x0A000012
#define WINAPI_FAMILY 100
#include <windows.h>
#include <stddef.h>
#define WF_STR2(x) #x
#define WF_STR(x) WF_STR2(x)
#pragma message("WF_MSC_VER=" WF_STR(_MSC_VER))
#pragma message("WF_MSC_FULL_VER=" WF_STR(_MSC_FULL_VER))
#pragma message("WF_WINAPI_FAMILY=" WF_STR(WINAPI_FAMILY))
#pragma message("WF_WIN32_WINNT=" WF_STR(_WIN32_WINNT))
#pragma message("WF_NTDDI_VERSION=" WF_STR(NTDDI_VERSION))
#pragma message("WF_WINAPI=" WF_STR(WINAPI))
#ifndef STARTF_USESTDHANDLES
#error WF_STARTF_MISSING
#endif
#ifndef PROC_THREAD_ATTRIBUTE_HANDLE_LIST
#error WF_HANDLE_LIST_MISSING
#endif
#ifndef PROC_THREAD_ATTRIBUTE_JOB_LIST
#error WF_JOB_LIST_MISSING
#endif
#ifdef _USE_FULL_PROC_THREAD_ATTRIBUTE
#error WF_UNEXPECTED_FULL_ATTRIBUTE_MACRO
#endif
#pragma message("WF_STARTF_USESTDHANDLES=" WF_STR(STARTF_USESTDHANDLES))
#pragma message("WF_HANDLE_LIST=" WF_STR(PROC_THREAD_ATTRIBUTE_HANDLE_LIST))
#pragma message("WF_JOB_LIST=" WF_STR(PROC_THREAD_ATTRIBUTE_JOB_LIST))
static_assert(_MSC_VER == 1950, "WF_MSC_VER_MISMATCH");
static_assert(_MSC_FULL_VER == 195035739, "WF_MSC_FULL_VER_MISMATCH");
static_assert(sizeof(void*) == 8, "WF_POINTER_SIZE_MISMATCH");
static_assert(sizeof(HANDLE) == 8, "WF_HANDLE_SIZE_MISMATCH");
static_assert(sizeof(STARTUPINFOW) == 104, "WF_STARTUPINFOW_SIZE_MISMATCH");
static_assert(alignof(STARTUPINFOW) == 8, "WF_STARTUPINFOW_ALIGN_MISMATCH");
static_assert(sizeof(STARTUPINFOEXW) == 112, "WF_STARTUPINFOEXW_SIZE_MISMATCH");
static_assert(alignof(STARTUPINFOEXW) == 8, "WF_STARTUPINFOEXW_ALIGN_MISMATCH");
static_assert(offsetof(STARTUPINFOW,cb) == 0, "WF_CB_OFFSET_MISMATCH");
static_assert(offsetof(STARTUPINFOW,dwFlags) == 60, "WF_FLAGS_OFFSET_MISMATCH");
static_assert(offsetof(STARTUPINFOW,hStdInput) == 80, "WF_STDIN_OFFSET_MISMATCH");
static_assert(offsetof(STARTUPINFOW,hStdOutput) == 88, "WF_STDOUT_OFFSET_MISMATCH");
static_assert(offsetof(STARTUPINFOW,hStdError) == 96, "WF_STDERR_OFFSET_MISMATCH");
static_assert(offsetof(STARTUPINFOEXW,lpAttributeList) == 104, "WF_ATTR_OFFSET_MISMATCH");
static_assert(STARTF_USESTDHANDLES == 0x00000100, "WF_STARTF_VALUE_MISMATCH");
using WF_CreateProcessW_ptr = decltype(&CreateProcessW);
using WF_InitAttributes_ptr = decltype(&InitializeProcThreadAttributeList);
using WF_UpdateAttributes_ptr = decltype(&UpdateProcThreadAttribute);
using WF_DeleteAttributes_ptr = decltype(&DeleteProcThreadAttributeList);
'@ | Set-Content -LiteralPath $Src -Encoding ASCII
  $ArgsList = @('/nologo','/Zs','/TP','/std:c++17','/X')
  foreach ($inc in $Includes) { $ArgsList += ('/I' + $inc) }
  $ArgsList += $Src
  Note 'STATIC_CHECK=START'
  $Raw = & $Cl @ArgsList 2>&1
  $Code = $LASTEXITCODE
  foreach ($line in $Raw) { Note ([string]$line) }
  Note "COMPILER_EXIT_CODE=$Code"
  if ($Code -ne 0) { throw "STATIC_CHECK_FAILED_EXIT=$Code" }
  Note 'WF_STATIC_ASSERTIONS=PASS'
  Note 'STATUS=PASS_COMPILE_ONLY_NO_LINK_NO_NATIVE_API'
} catch {
  Note ('STATUS=STOP; REASON=' + $_.Exception.Message)
} finally {
  if ($Temp -and (Test-Path -LiteralPath $Temp)) {
    Remove-Item -LiteralPath $Temp -Recurse -Force -ErrorAction SilentlyContinue
    Note ('TEMP_REMOVED=' + (-not (Test-Path -LiteralPath $Temp)))
  }
  $Log | Set-Content -LiteralPath $Output -Encoding UTF8
  Note "REPORT_PATH=$Output"
  Note 'CONTROLLER_ABI_PIN=NOT_RATIFIED; REAL_WINDOWS_EXECUTION=NOT_AUTHORIZED; FULL_INR_READY=NO'
}
