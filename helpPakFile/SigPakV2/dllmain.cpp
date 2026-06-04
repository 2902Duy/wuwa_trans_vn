#include <windows.h>
#include <iostream>
#include <string>
#include <thread>
#include "interceptor.hpp"
#include "logger.h"

// Pointer to original function in kernelbase.dll to call after intercepting
typedef HANDLE(WINAPI* PCreateFileW)(
    LPCWSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
    );

PCreateFileW CreateFileW_Original = nullptr;


namespace SigGate {
    const std::wstring ext = L".sig";
    const std::wstring ue_p_suffix = L"WindowsNoEditor_P.sig";
    const std::wstring ue_suffix = L"WindowsNoEditor.sig";

    // Callback function to be called instead of CreateFileW
    HANDLE WINAPI callback(
        LPCWSTR lpFileName,
        DWORD dwDesiredAccess,
        DWORD dwShareMode,
        LPSECURITY_ATTRIBUTES lpSecurityAttributes,
        DWORD dwCreationDisposition,
        DWORD dwFlagsAndAttributes,
        HANDLE hTemplateFile
    ) {
        std::wstring file_name(lpFileName);

        // Logic to check for .sig extension but exclude Unreal Engine files
        if (file_name.size() >= 4 && file_name.substr(file_name.size() - 4) == ext) {
            if (file_name.find(ue_suffix) == std::wstring::npos &&
                file_name.find(ue_p_suffix) == std::wstring::npos) {

                LOG_SUCCESS("Hit CreateFileW: %ls - Suspending thread!\n", lpFileName);
                // Suspend current thread if conditions are met
                SuspendThread(GetCurrentThread());
            }
        }

        // Call original CreateFileW function to continue game execution
        return CreateFileW_Original(
            lpFileName, dwDesiredAccess, dwShareMode,
            lpSecurityAttributes, dwCreationDisposition,
            dwFlagsAndAttributes, hTemplateFile
        );
    }
}

bool IsMyGameWindow(HWND hwnd) {
    DWORD windowPid = 0;
    GetWindowThreadProcessId(hwnd, &windowPid); // Get PID of the found window
    return windowPid == GetCurrentProcessId(); // Compare with own PID
}

void onAttach(HMODULE Module) {
    Logger::Init("wuwaVietHoa");
    AllocConsole();
    //FILE* f;
    //freopen_s(&f, "CONOUT$", "w", stdout);

    LOG_INFO("Waiting for wuwaVietHoa: Custom Mod Loader\n");

    // Get CreateFileW function address from kernelbase.dll and kernel32.dll
    HMODULE hKernelBase = GetModuleHandleW(L"kernelbase.dll");
    CreateFileW_Original = (PCreateFileW)GetProcAddress(hKernelBase, "CreateFileW");

    HMODULE hKernel32 = GetModuleHandleW(L"kernel32.dll");
    uintptr_t create_file_w_addr = (uintptr_t)GetProcAddress(hKernel32, "CreateFileW");

    // Perform function interception/hook
    if (Interceptor::replace(create_file_w_addr, (void*)SigGate::callback) != Interceptor::Error::Success) {
        LOG_ERROR("Failed to intercept CreateFileW!\n");
        exit(1);
    }
    LOG_SUCCESS("Success!\n");
    
    /*while (!FindWindowA("UnrealWindow", 0)) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }*/
    HWND targetHwnd = NULL;

    // Loop until the correct window of this process is found
    while (true) {
        // Find window with class UnrealWindow
        targetHwnd = FindWindowA("UnrealWindow", NULL);

        if (targetHwnd != NULL) {
            // If found, check if it belongs to the game we are injecting
            if (IsMyGameWindow(targetHwnd)) {
                break; // Correct window of this game, exit loop
            }
        }

        // If not or not found yet, sleep 100ms and try again
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    LOG_WARNING("Please click X on this window to EXIT GAME");
    Interceptor::restore();
    //FreeConsole();
    FreeLibraryAndExitThread(Module, 0);
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        CreateThread(0, 0, (LPTHREAD_START_ROUTINE)onAttach, hModule, 0, 0);
    }
    return TRUE;
}