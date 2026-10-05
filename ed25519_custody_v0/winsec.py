"""Windows-native security primitives for the Ed25519 custody helper v0.

Directories are created with an explicit protected DACL supplied atomically
at creation. Owner and DACL are verified through handles. Secret-bearing
files are created new inside an already protected directory and inherit its
DACL. ACLs do not protect against same-user compromise or administrators.
"""

from __future__ import annotations

import ctypes
import os
import sys
import uuid
from ctypes import wintypes
from dataclasses import dataclass

from .errors import fail

if sys.platform != "win32":  # pragma: no cover
    raise ImportError("ed25519_custody_v0 is Windows-only")

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_adv = ctypes.WinDLL("advapi32", use_last_error=True)
_shell = ctypes.WinDLL("shell32", use_last_error=True)
_ole = ctypes.WinDLL("ole32", use_last_error=True)

_HANDLE = wintypes.HANDLE
_INVALID_HANDLE = ctypes.c_void_p(-1).value

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
READ_CONTROL = 0x00020000
FILE_READ_ATTRIBUTES = 0x00000080
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
FILE_SHARE_DELETE = 0x4
CREATE_NEW = 1
OPEN_EXISTING = 3
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
MOVEFILE_REPLACE_EXISTING = 0x1
MOVEFILE_WRITE_THROUGH = 0x8
SE_FILE_OBJECT = 1
OWNER_SECURITY_INFORMATION = 0x1
DACL_SECURITY_INFORMATION = 0x4
SE_DACL_PROTECTED = 0x1000
ACCESS_ALLOWED_ACE_TYPE = 0
OBJECT_INHERIT_ACE = 0x1
CONTAINER_INHERIT_ACE = 0x2
INHERITED_ACE = 0x10
FILE_ALL_ACCESS = 0x001F01FF
DRIVE_FIXED = 3
TOKEN_QUERY = 0x8
TOKEN_USER_CLASS = 1
TOKEN_GROUPS_CLASS = 2
TOKEN_ELEVATION_TYPE_CLASS = 18
TOKEN_ELEVATION_CLASS = 20
TOKEN_ELEVATION_TYPE_DEFAULT = 1
ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_FILE_EXISTS = 80
ERROR_ALREADY_EXISTS = 183
ERROR_NO_TOKEN = 1008
HRESULT_NOT_IN_SYNC_ROOT = 0x80070186
SYSTEM_SID = "S-1-5-18"
MAX_PATH_CHARS = 32768

FOLDERID_LOCAL_APPDATA = "F1B32785-6FBA-4FCF-9D55-7B8E7F157091"
FOLDERID_PROFILE = "5E6C858F-0E22-4760-9AFE-EA3317B67173"
FOLDERID_ROAMING_APPDATA = "3EB685DB-65F9-4CF6-A03A-E3EF65729F3D"

_FORBIDDEN_GROUP_SIDS = frozenset(
    {
        "S-1-5-32-544",  # BUILTIN\Administrators
        "S-1-5-114",  # local account and member of Administrators
        "S-1-5-32-551",  # Backup Operators
        "S-1-5-32-549",  # Server Operators
        "S-1-5-6",  # SERVICE
    }
)
_FORBIDDEN_DOMAIN_RIDS = ("-512", "-518", "-519")
_FORBIDDEN_USER_SIDS = frozenset({"S-1-5-18", "S-1-5-19", "S-1-5-20"})


class _SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", ctypes.c_void_p),
        ("bInheritHandle", wintypes.BOOL),
    ]


class _ACE_HEADER(ctypes.Structure):
    _fields_ = [
        ("AceType", ctypes.c_ubyte),
        ("AceFlags", ctypes.c_ubyte),
        ("AceSize", wintypes.WORD),
    ]


class _ACCESS_ALLOWED_ACE(ctypes.Structure):
    _fields_ = [
        ("Header", _ACE_HEADER),
        ("Mask", wintypes.DWORD),
        ("SidStart", wintypes.DWORD),
    ]


class _ACL_SIZE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("AceCount", wintypes.DWORD),
        ("AclBytesInUse", wintypes.DWORD),
        ("AclBytesFree", wintypes.DWORD),
    ]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]


def _proto(dll, name, restype, argtypes):
    fn = getattr(dll, name)
    fn.restype = restype
    fn.argtypes = argtypes
    return fn


_GetCurrentProcess = _proto(_k32, "GetCurrentProcess", _HANDLE, [])
_GetCurrentThread = _proto(_k32, "GetCurrentThread", _HANDLE, [])
_CloseHandle = _proto(_k32, "CloseHandle", wintypes.BOOL, [_HANDLE])
_LocalFree = _proto(_k32, "LocalFree", ctypes.c_void_p, [ctypes.c_void_p])
_CreateDirectoryW = _proto(
    _k32,
    "CreateDirectoryW",
    wintypes.BOOL,
    [wintypes.LPCWSTR, ctypes.POINTER(_SECURITY_ATTRIBUTES)],
)
_CreateFileW = _proto(
    _k32,
    "CreateFileW",
    _HANDLE,
    [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        _HANDLE,
    ],
)
_ReadFile = _proto(
    _k32,
    "ReadFile",
    wintypes.BOOL,
    [_HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p],
)
_WriteFile = _proto(
    _k32,
    "WriteFile",
    wintypes.BOOL,
    [_HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p],
)
_FlushFileBuffers = _proto(_k32, "FlushFileBuffers", wintypes.BOOL, [_HANDLE])
_GetFileInformationByHandle = _proto(
    _k32,
    "GetFileInformationByHandle",
    wintypes.BOOL,
    [_HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION)],
)
_GetFinalPathNameByHandleW = _proto(
    _k32,
    "GetFinalPathNameByHandleW",
    wintypes.DWORD,
    [_HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD],
)
_GetFileAttributesW = _proto(_k32, "GetFileAttributesW", wintypes.DWORD, [wintypes.LPCWSTR])
_GetDriveTypeW = _proto(_k32, "GetDriveTypeW", wintypes.UINT, [wintypes.LPCWSTR])
_MoveFileExW = _proto(
    _k32, "MoveFileExW", wintypes.BOOL, [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
)
_DeleteFileW = _proto(_k32, "DeleteFileW", wintypes.BOOL, [wintypes.LPCWSTR])
_RemoveDirectoryW = _proto(_k32, "RemoveDirectoryW", wintypes.BOOL, [wintypes.LPCWSTR])
_GetTempPathW = _proto(_k32, "GetTempPathW", wintypes.DWORD, [wintypes.DWORD, wintypes.LPWSTR])
_OpenProcessToken = _proto(
    _adv, "OpenProcessToken", wintypes.BOOL, [_HANDLE, wintypes.DWORD, ctypes.POINTER(_HANDLE)]
)
_OpenThreadToken = _proto(
    _adv,
    "OpenThreadToken",
    wintypes.BOOL,
    [_HANDLE, wintypes.DWORD, wintypes.BOOL, ctypes.POINTER(_HANDLE)],
)
_GetTokenInformation = _proto(
    _adv,
    "GetTokenInformation",
    wintypes.BOOL,
    [_HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)],
)
_ConvertSidToStringSidW = _proto(
    _adv, "ConvertSidToStringSidW", wintypes.BOOL, [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
)
_ConvertStringSecurityDescriptorToSecurityDescriptorW = _proto(
    _adv,
    "ConvertStringSecurityDescriptorToSecurityDescriptorW",
    wintypes.BOOL,
    [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p],
)
_GetSecurityInfo = _proto(
    _adv,
    "GetSecurityInfo",
    wintypes.DWORD,
    [
        _HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ],
)
_GetSecurityDescriptorControl = _proto(
    _adv,
    "GetSecurityDescriptorControl",
    wintypes.BOOL,
    [ctypes.c_void_p, ctypes.POINTER(wintypes.WORD), ctypes.POINTER(wintypes.DWORD)],
)
_GetAclInformation = _proto(
    _adv,
    "GetAclInformation",
    wintypes.BOOL,
    [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_int],
)
_GetAce = _proto(
    _adv, "GetAce", wintypes.BOOL, [ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)]
)
_SHGetKnownFolderPath = _proto(
    _shell,
    "SHGetKnownFolderPath",
    ctypes.c_long,
    [ctypes.POINTER(_GUID), wintypes.DWORD, _HANDLE, ctypes.POINTER(ctypes.c_void_p)],
)
_CoTaskMemFree = _proto(_ole, "CoTaskMemFree", None, [ctypes.c_void_p])


def _last_error() -> int:
    return ctypes.get_last_error()


def _sid_to_string(psid) -> str:
    out = ctypes.c_void_p()
    if not psid or not _ConvertSidToStringSidW(psid, ctypes.byref(out)):
        fail("ACL_REJECTED")
    try:
        return ctypes.wstring_at(out.value)
    finally:
        _LocalFree(out)


# ---------------------------------------------------------------- account


@dataclass(frozen=True)
class TokenFacts:
    user_sid: str
    elevated: bool
    elevation_type: int
    group_sids: tuple
    impersonating: bool


def _token_buffer(token, cls):
    needed = wintypes.DWORD()
    _GetTokenInformation(token, cls, None, 0, ctypes.byref(needed))
    if needed.value == 0 or needed.value > 1 << 20:
        fail("ACCOUNT_REJECTED")
    buf = ctypes.create_string_buffer(needed.value)
    if not _GetTokenInformation(token, cls, buf, needed, ctypes.byref(needed)):
        fail("ACCOUNT_REJECTED")
    return buf


def _token_facts() -> TokenFacts:
    token = _HANDLE()
    if not _OpenProcessToken(_GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)):
        fail("ACCOUNT_REJECTED")
    try:
        user_buf = _token_buffer(token, TOKEN_USER_CLASS)
        user = _SID_AND_ATTRIBUTES.from_buffer(user_buf)
        user_sid = _sid_to_string(user.Sid)
        elevated = int.from_bytes(_token_buffer(token, TOKEN_ELEVATION_CLASS).raw[:4], "little")
        etype = int.from_bytes(_token_buffer(token, TOKEN_ELEVATION_TYPE_CLASS).raw[:4], "little")
        groups_buf = _token_buffer(token, TOKEN_GROUPS_CLASS)
        count = ctypes.c_uint32.from_buffer(groups_buf).value
        offset = ctypes.sizeof(ctypes.c_void_p)
        if offset + count * ctypes.sizeof(_SID_AND_ATTRIBUTES) > len(groups_buf):
            fail("ACCOUNT_REJECTED")
        array = (_SID_AND_ATTRIBUTES * count).from_buffer(groups_buf, offset)
        groups = tuple(_sid_to_string(entry.Sid) for entry in array)
    finally:
        _CloseHandle(token)
    thread_token = _HANDLE()
    if _OpenThreadToken(_GetCurrentThread(), TOKEN_QUERY, True, ctypes.byref(thread_token)):
        _CloseHandle(thread_token)
        impersonating = True
    else:
        impersonating = _last_error() != ERROR_NO_TOKEN
    return TokenFacts(user_sid, bool(elevated), etype, groups, impersonating)


def evaluate_account(facts: TokenFacts) -> str:
    """Accept only a non-elevated, non-admin, non-service, non-impersonated user."""
    sid = facts.user_sid
    if type(sid) is not str or not sid.startswith("S-1-5-21-"):
        fail("ACCOUNT_REJECTED")
    if sid in _FORBIDDEN_USER_SIDS:
        fail("ACCOUNT_REJECTED")
    if facts.elevated:
        fail("ACCOUNT_REJECTED")
    if facts.elevation_type != TOKEN_ELEVATION_TYPE_DEFAULT:
        fail("ACCOUNT_REJECTED")
    if facts.impersonating:
        fail("ACCOUNT_REJECTED")
    for group in facts.group_sids:
        if group in _FORBIDDEN_GROUP_SIDS:
            fail("ACCOUNT_REJECTED")
        if group.startswith("S-1-5-21-") and group.endswith(_FORBIDDEN_DOMAIN_RIDS):
            fail("ACCOUNT_REJECTED")
    return sid


def check_account() -> str:
    return evaluate_account(_token_facts())


# ---------------------------------------------------------------- locations


def known_folder(folder_id: str) -> str:
    guid = _GUID.from_buffer_copy(uuid.UUID(folder_id).bytes_le)
    out = ctypes.c_void_p()
    if _SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(out)) != 0:
        if out.value:
            _CoTaskMemFree(out)
        fail("PATH_REJECTED")
    try:
        return ctypes.wstring_at(out.value)
    finally:
        _CoTaskMemFree(out)


def temp_path() -> str:
    buf = ctypes.create_unicode_buffer(MAX_PATH_CHARS)
    n = _GetTempPathW(MAX_PATH_CHARS, buf)
    if n == 0 or n >= MAX_PATH_CHARS:
        fail("PATH_REJECTED")
    return buf.value.rstrip("\\")


def file_attributes(path: str):
    """Return attributes without following the final component, or None if absent."""
    attrs = _GetFileAttributesW(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        if _last_error() in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
            return None
        fail("PATH_REJECTED")
    return attrs


def drive_type(root: str) -> int:
    return int(_GetDriveTypeW(root))


def sync_root_hresult(path: str) -> int:
    try:
        cld = ctypes.WinDLL("cldapi", use_last_error=True)
        fn = _proto(
            cld,
            "CfGetSyncRootInfoByPath",
            ctypes.c_long,
            [wintypes.LPCWSTR, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)],
        )
    except (OSError, AttributeError):
        fail("PATH_REJECTED")
    buf = ctypes.create_string_buffer(256)
    returned = wintypes.DWORD()
    return fn(path, 0, buf, 256, ctypes.byref(returned)) & 0xFFFFFFFF


def list_entries(path: str) -> dict:
    """Map entry name to attributes for one directory, without following links."""
    entries = {}
    with os.scandir(path) as it:
        for entry in it:
            entries[entry.name] = entry.stat(follow_symlinks=False).st_file_attributes
    return entries


# ---------------------------------------------------------------- security


def protected_sddl(user_sid: str) -> str:
    return "O:" + user_sid + "D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;" + user_sid + ")"


def _expected_aces(user_sid: str, flags: int) -> list:
    return sorted(
        [
            (ACCESS_ALLOWED_ACE_TYPE, flags, FILE_ALL_ACCESS, SYSTEM_SID),
            (ACCESS_ALLOWED_ACE_TYPE, flags, FILE_ALL_ACCESS, user_sid),
        ]
    )


def evaluate_directory_acl(owner: str, control: int, aces: tuple, user_sid: str) -> None:
    """Protected explicit DACL: intended user plus SYSTEM, OICI full access only."""
    if owner != user_sid:
        fail("ACL_REJECTED")
    if not control & SE_DACL_PROTECTED:
        fail("ACL_REJECTED")
    if sorted(aces) != _expected_aces(user_sid, OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE):
        fail("ACL_REJECTED")


def evaluate_file_acl(owner: str, control: int, aces: tuple, user_sid: str) -> None:
    """N1: a file carries only the ACEs inherited from its protected directory."""
    if owner != user_sid:
        fail("ACL_REJECTED")
    if control & SE_DACL_PROTECTED:
        fail("ACL_REJECTED")
    if sorted(aces) != _expected_aces(user_sid, INHERITED_ACE):
        fail("ACL_REJECTED")


def _security_of_handle(handle):
    owner = ctypes.c_void_p()
    dacl = ctypes.c_void_p()
    psd = ctypes.c_void_p()
    rc = _GetSecurityInfo(
        handle,
        SE_FILE_OBJECT,
        OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(psd),
    )
    if rc != 0:
        fail("ACL_REJECTED")
    try:
        if not dacl.value:
            fail("ACL_REJECTED")
        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if not _GetSecurityDescriptorControl(psd, ctypes.byref(control), ctypes.byref(revision)):
            fail("ACL_REJECTED")
        info = _ACL_SIZE_INFORMATION()
        if not _GetAclInformation(dacl, ctypes.byref(info), ctypes.sizeof(info), 2):
            fail("ACL_REJECTED")
        aces = []
        for index in range(info.AceCount):
            pace = ctypes.c_void_p()
            if not _GetAce(dacl, index, ctypes.byref(pace)):
                fail("ACL_REJECTED")
            header = _ACE_HEADER.from_address(pace.value)
            if header.AceType != ACCESS_ALLOWED_ACE_TYPE:
                aces.append((header.AceType, header.AceFlags, 0, ""))
                continue
            ace = _ACCESS_ALLOWED_ACE.from_address(pace.value)
            sid = _sid_to_string(pace.value + _ACCESS_ALLOWED_ACE.SidStart.offset)
            aces.append((header.AceType, header.AceFlags, ace.Mask, sid))
        return _sid_to_string(owner.value), control.value, tuple(aces)
    finally:
        _LocalFree(psd)


@dataclass(frozen=True)
class HandleInfo:
    attributes: int
    links: int
    size: int
    identity: tuple
    final_path: str


def _handle_info(handle) -> HandleInfo:
    info = _BY_HANDLE_FILE_INFORMATION()
    if not _GetFileInformationByHandle(handle, ctypes.byref(info)):
        fail("FILE_REJECTED")
    buf = ctypes.create_unicode_buffer(MAX_PATH_CHARS)
    n = _GetFinalPathNameByHandleW(handle, buf, MAX_PATH_CHARS, 0)
    if n == 0 or n >= MAX_PATH_CHARS:
        fail("FILE_REJECTED")
    final = buf.value
    if final.startswith("\\\\?\\UNC\\"):
        fail("PATH_REJECTED")
    if final.startswith("\\\\?\\"):
        final = final[4:]
    return HandleInfo(
        info.dwFileAttributes,
        info.nNumberOfLinks,
        (info.nFileSizeHigh << 32) | info.nFileSizeLow,
        (info.dwVolumeSerialNumber, info.nFileIndexHigh, info.nFileIndexLow),
        final,
    )


def _same_path(a: str, b: str) -> bool:
    return os.path.normcase(a) == os.path.normcase(b)


def _open(path: str, access: int, share: int, disposition: int, flags: int):
    handle = _CreateFileW(path, access, share, None, disposition, flags, None)
    if handle is None or handle == _INVALID_HANDLE:
        return None, _last_error()
    return handle, 0


def verify_directory(path: str, user_sid: str) -> None:
    handle, _err = _open(
        path,
        READ_CONTROL | FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
    )
    if handle is None:
        fail("PATH_REJECTED")
    try:
        info = _handle_info(handle)
        if info.attributes & FILE_ATTRIBUTE_REPARSE_POINT:
            fail("PATH_REJECTED")
        if not info.attributes & FILE_ATTRIBUTE_DIRECTORY:
            fail("PATH_REJECTED")
        if not _same_path(info.final_path, path):
            fail("PATH_REJECTED")
        owner, control, aces = _security_of_handle(handle)
        evaluate_directory_acl(owner, control, aces, user_sid)
    finally:
        _CloseHandle(handle)


def create_protected_directory(path: str, user_sid: str) -> None:
    """Create one directory with its protected DACL supplied at creation."""
    psd = ctypes.c_void_p()
    if not _ConvertStringSecurityDescriptorToSecurityDescriptorW(
        protected_sddl(user_sid), 1, ctypes.byref(psd), None
    ):
        fail("ACL_REJECTED")
    try:
        attrs = _SECURITY_ATTRIBUTES(ctypes.sizeof(_SECURITY_ATTRIBUTES), psd.value, False)
        if not _CreateDirectoryW(path, ctypes.byref(attrs)):
            if _last_error() == ERROR_ALREADY_EXISTS:
                fail("EXISTS_REJECTED")
            fail("PATH_REJECTED")
    finally:
        _LocalFree(psd)
    verify_directory(path, user_sid)


def _verify_open_file(handle, path: str, user_sid: str) -> HandleInfo:
    info = _handle_info(handle)
    if info.attributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY):
        fail("FILE_REJECTED")
    if info.links != 1:
        fail("FILE_REJECTED")
    if not _same_path(info.final_path, path):
        fail("FILE_REJECTED")
    owner, control, aces = _security_of_handle(handle)
    evaluate_file_acl(owner, control, aces, user_sid)
    return info


def write_new_file(path: str, user_sid: str, data: bytes) -> None:
    """Create-new, verify inherited owner/DACL before content, write, flush, close, reverify."""
    if type(data) is not bytes:
        fail("FILE_REJECTED")
    handle, err = _open(
        path,
        GENERIC_WRITE | READ_CONTROL | FILE_READ_ATTRIBUTES,
        0,
        CREATE_NEW,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OPEN_REPARSE_POINT,
    )
    if handle is None:
        if err in (ERROR_FILE_EXISTS, ERROR_ALREADY_EXISTS):
            fail("EXISTS_REJECTED")
        fail("FILE_REJECTED")
    try:
        info = _verify_open_file(handle, path, user_sid)
        if info.size != 0:
            fail("FILE_REJECTED")
        buf = ctypes.create_string_buffer(data, len(data))
        written = wintypes.DWORD()
        if not _WriteFile(handle, buf, len(data), ctypes.byref(written), None):
            fail("FILE_REJECTED")
        if written.value != len(data):
            fail("FILE_REJECTED")
        if not _FlushFileBuffers(handle):
            fail("FILE_REJECTED")
    finally:
        _CloseHandle(handle)
    read_file(path, user_sid, len(data))


def read_file(path: str, user_sid: str, max_size: int):
    """Read one regular, single-link, non-reparse file with verified owner/DACL."""
    handle, _err = _open(
        path,
        GENERIC_READ | READ_CONTROL,
        FILE_SHARE_READ,
        OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT,
    )
    if handle is None:
        fail("FILE_REJECTED")
    try:
        info = _verify_open_file(handle, path, user_sid)
        if info.size > max_size:
            fail("FILE_REJECTED")
        size = info.size
        buf = ctypes.create_string_buffer(size + 1)
        got = wintypes.DWORD()
        if not _ReadFile(handle, buf, size + 1, ctypes.byref(got), None):
            fail("FILE_REJECTED")
        if got.value != size:
            fail("FILE_REJECTED")
        return buf.raw[:size], info.identity
    finally:
        _CloseHandle(handle)


def replace_file(source: str, destination: str) -> None:
    if not _MoveFileExW(source, destination, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH):
        fail("FILE_REJECTED")


def move_no_replace(source: str, destination: str) -> None:
    if not _MoveFileExW(source, destination, MOVEFILE_WRITE_THROUGH):
        fail("FILE_REJECTED")


def delete_file(path: str) -> None:
    if not _DeleteFileW(path):
        fail("FILE_REJECTED")


def remove_directory(path: str) -> None:
    if not _RemoveDirectoryW(path):
        fail("FILE_REJECTED")
