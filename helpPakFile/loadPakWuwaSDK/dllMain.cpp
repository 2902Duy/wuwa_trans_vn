#include <Windows.h>
#include <iostream>
#include "logger.h"
#include "SDK/Engine_classes.hpp"
#include "SDK/KuroHotPatch_classes.hpp"
#include <filesystem>
namespace fs = std::filesystem;

bool CheckMountPak()
{
    SDK::UFunction* MountPakFunc = SDK::UKuroPakMountStatic::StaticClass()->GetFunction("KuroPakMountStatic", "MountPak");
    if (!MountPakFunc)
        return false;
    return true;
}

void unloadHook(HMODULE hModule) {
    Sleep(1000);// Standard timing
    FreeConsole();
    FreeLibraryAndExitThread(hModule, 0);
}

bool EnsureFolderExists(const std::string& folderPath) {
    if (!fs::exists(folderPath)) {
        LOG_ERROR("Directory does not exist. Creating folder...");
        if (fs::create_directories(folderPath))
        {
            LOG_SUCCESS("Folder created successfully");
            return true;
        }
        else
        {
            return false;
        }
    }
    return true; // already exists
}



bool ProcessPakFiles(const std::string& folderPath) {
    if (!fs::exists(folderPath) || !fs::is_directory(folderPath)) {
        LOG_ERROR("Directory does not exist or is invalid.\n");
        return false;
    }

    int idCounter = 46; // dummy ID value
    bool foundPak = false;
    Sleep(3000);// Standard timing
    for (const auto& entry : fs::directory_iterator(folderPath)) {
        if (entry.is_regular_file() && entry.path().extension() == ".pak") {
            foundPak = true;
            std::wstring wpath = entry.path().wstring();
            SDK::UKuroPakMountStatic::MountPak(wpath.c_str(), idCounter);
            LOG_SUCCESS("load pak: %ws", wpath.c_str());
            SDK::UKuroPakMountStatic::RemoveSha1Check(wpath.c_str());
            idCounter++;
        }
    }

    if (!foundPak) {
        LOG_ERROR("No *.pak files found in directory.\n");
        return false;
    }
    else
    {
        return true;
    }
}

std::string GetCurrentDllDirectory(HMODULE hModule) {
    char buffer[MAX_PATH];
    GetModuleFileNameA(hModule, buffer, MAX_PATH); // get DLL path
    return fs::path(buffer).parent_path().string(); // get DLL directory
}

DWORD MainThread(HMODULE Module)
{
    Logger::Init("Log");
    LOG_SUCCESS("Wuthering Waves Vietnamese Mod Loader Loaded!");

    while (true)
    {
        if (CheckMountPak())
        {
            LOG_INFO("[+] Pak Load valid!\n");
            break; // or continue processing
        }
        else
        {
            //LOG_INFO("[-] Waiting for objects...\n");
        }

        Sleep(100);
    }

    std::filesystem::path dllPath = GetCurrentDllDirectory(Module);
    dllPath /= "wuwaVietHoa";
    std::string pathVietHoa = dllPath.string();
    if (EnsureFolderExists(pathVietHoa)) {
        LOG_INFO("Directory is ready: %s \n", pathVietHoa.c_str());
    }
    else {
        LOG_ERROR("Could not create directory: %s\n", pathVietHoa.c_str());
    }

    if (!ProcessPakFiles(pathVietHoa))
    {
        LOG_ERROR("No .pak files found or directory inaccessible.\n");
        LOG_WARNING("Exiting game in 5s.\n");
        Sleep(5000);
        ExitProcess(1);
    }
    unloadHook(Module);
    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved)
{
    switch (reason)
    {
    case DLL_PROCESS_ATTACH:
        CreateThread(0, 0, (LPTHREAD_START_ROUTINE)MainThread, hModule, 0, 0);
        break;
    }

    return TRUE;
}