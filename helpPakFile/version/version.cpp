#include <windows.h>

// Forward all 17 standard functions of version.dll to version_orig.dll
#pragma comment(linker, "/export:GetFileVersionInfoA=version_orig.GetFileVersionInfoA,@1")
#pragma comment(linker, "/export:GetFileVersionInfoByHandle=version_orig.GetFileVersionInfoByHandle,@2")
#pragma comment(linker, "/export:GetFileVersionInfoExA=version_orig.GetFileVersionInfoExA,@3")
#pragma comment(linker, "/export:GetFileVersionInfoExW=version_orig.GetFileVersionInfoExW,@4")
#pragma comment(linker, "/export:GetFileVersionInfoSizeA=version_orig.GetFileVersionInfoSizeA,@5")
#pragma comment(linker, "/export:GetFileVersionInfoSizeExA=version_orig.GetFileVersionInfoSizeExA,@6")
#pragma comment(linker, "/export:GetFileVersionInfoSizeExW=version_orig.GetFileVersionInfoSizeExW,@7")
#pragma comment(linker, "/export:GetFileVersionInfoSizeW=version_orig.GetFileVersionInfoSizeW,@8")
#pragma comment(linker, "/export:GetFileVersionInfoW=version_orig.GetFileVersionInfoW,@9")
#pragma comment(linker, "/export:VerFindFileA=version_orig.VerFindFileA,@10")
#pragma comment(linker, "/export:VerFindFileW=version_orig.VerFindFileW,@11")
#pragma comment(linker, "/export:VerInstallFileA=version_orig.VerInstallFileA,@12")
#pragma comment(linker, "/export:VerInstallFileW=version_orig.VerInstallFileW,@13")
#pragma comment(linker, "/export:VerLanguageNameA=version_orig.VerLanguageNameA,@14")
#pragma comment(linker, "/export:VerLanguageNameW=version_orig.VerLanguageNameW,@15")
#pragma comment(linker, "/export:VerQueryValueA=version_orig.VerQueryValueA,@16")
#pragma comment(linker, "/export:VerQueryValueW=version_orig.VerQueryValueW,@17")

DWORD WINAPI LoadPayloadThread(LPVOID lpParam)
{
    // Sleep a tiny bit to let the loader lock release
    Sleep(100);
    LoadLibraryW(L"wuwaVietHoa.dll");
    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved)
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        CreateThread(NULL, 0, LoadPayloadThread, NULL, 0, NULL);
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
