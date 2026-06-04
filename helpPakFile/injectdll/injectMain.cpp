#include "findAndKillGame.h"
#include "openGame.h"
#include "inject.h"

const std::string GlobalWuwaProcName = "Client-Win64-Shipping.exe";
const char* DLLPath = "wuwaVietHoa.dll";
int chooseOption = 0;

void chooseInjectMethod()
{
	do
	{
		std::cout << ("[+] Select Inject Method: [1].Launch game & Inject | [2].Wait for game to launch & Inject") << std::endl;
		std::cout << ("[-] Enter Your Choice: ");
		std::cin >> chooseOption;

		// Check if input is not a number
		if (std::cin.fail())
		{
			std::cin.clear();            // Clear error state
			std::cin.ignore(1000, '\n'); // Ignore invalid characters in input buffer
			std::cout << ("[!] Invalid choice. Try again.") << std::endl;
		}
		else if ((chooseOption < 1 || chooseOption > 2))
		{
			std::cout << ("[!] Invalid choice. Try again.") << std::endl;
		}
	} while (chooseOption < 1 || chooseOption > 2 || std::cin.fail());
	if (chooseOption == 2)
	{
		ini.SetBoolValue("Inject", "suDungChoMoGame", true);
		ini.SaveFile("cfg.ini");
	}
	else
	{
		ini.SetBoolValue("Inject", "suDungChoMoGame", false);
		ini.SaveFile("cfg.ini");
	}
}

int main()
{
	if (!std::filesystem::exists("wuwaVietHoa.dll"))
	{
		std::cout << "Rename DLL to wuwaVietHoa.dll \nPlace it in the same directory as the Injector." << std::endl;
		system("pause");
		killLoader();
	}

    WaitForCloseProcess(GlobalWuwaProcName);
	Sleep(1000);
    ini.SetUnicode();
    ini.LoadFile("cfg.ini");
	std::string suDungChoMoGameKey = ini.GetValue("Inject", "suDungChoMoGame","");
	if (suDungChoMoGameKey.empty()) {
		chooseInjectMethod();		
	}

	HANDLE hProcess, hThread;
	bool suDungChoMoGame = ini.GetBoolValue("Inject", "suDungChoMoGame");
	int pidwuwa = NULL;
	system("cls");

	if (suDungChoMoGame)
	{
		std::cout << "Waiting for game to launch..." << std::endl;
		while (pidwuwa == -1 || pidwuwa == NULL)
		{
			pidwuwa = FindProcessId(GlobalWuwaProcName);			
			Sleep(50);
		}
		hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pidwuwa);

	}
	else
	{
		bool success = OpenGameProcess(&hProcess, &hThread, " Client -dx11 -DisableModule=streamline -freeopenlog");
		if (!success)
		{
			std::cout << "Could not open Client-Win64-Shipping process." << std::endl;
			system("pause");
			killLoader();
		}
	}

	ini.SaveFile("cfg.ini");
	std::string filename = DLLPath;
	std::filesystem::path currentDllPath = std::filesystem::current_path() / filename;
	LoadLibraryDLL(hProcess, currentDllPath.string());
	if (!suDungChoMoGame)
	{
		ResumeThread(hThread);
	}
	//system("pause");
	CloseHandle(hProcess);
}