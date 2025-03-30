import os
import sys
import time
import psutil
import servicemanager
import win32serviceutil
import win32service
import win32event
import subprocess

# Настройки
BLOCKED_PROCESSES = [
    "RobloxPlayerInstaller.exe",
    "RobloxStudioInstaller.exe",
    "RobloxPlayerBeta.exe",
    "RobloxCrashHandler.exe",
    "CrashHandler.exe",
    "Windows10Universal.exe"
]

ROBLOX_FOLDER_PATH = os.path.join(os.getenv("LOCALAPPDATA"), "Roblox")

def load_env(filepath=".env"):
    """
    Загрузка переменных среды из файла .env.
    Формат файла: каждая строка содержит ключ и значение, разделённые знаком "=".
    Пример: User=Игрок1
    """
    if os.path.exists(filepath):
        print(f"Загрузка переменных из {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
                    print(f'Установлена переменная: {key}={value}')
    else:
        print("Файл .env не найден. Переменные не загружены.")

def kill_processes():
    """Завершает процессы, связанные с Roblox. Возвращает True если процессы были найдены."""
    try:
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            process_name = proc.info['name']
            if process_name and any(keyword.lower() in process_name.lower() for keyword in BLOCKED_PROCESSES):
                print(f"Завершение процесса {process_name} (PID: {proc.info['pid']})...")
                subprocess.run(["taskkill", "/PID", str(proc.info['pid']), "/F"], check=True)
                found = True
            else:
                print(f"Процесс {process_name} (PID: {proc.info['pid']}) не был найден в списке заблокированных процессов.")
        return found
    except Exception as e:
        print(f"Ошибка при завершении процесса: {e}")
        return False

def remove_roblox_folder():
    """Находит и удаляет папку Roblox в AppData."""
    try:
        if os.path.exists(ROBLOX_FOLDER_PATH):
            print(f"Удаление папки Roblox: {ROBLOX_FOLDER_PATH}")
            for root, dirs, files in os.walk(ROBLOX_FOLDER_PATH, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    os.chmod(file_path, 0o777)
                    os.remove(file_path)
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    os.chmod(dir_path, 0o777)
                    os.rmdir(dir_path)
            os.rmdir(ROBLOX_FOLDER_PATH)
        else:
            print(f"Папка Roblox не найдена: {ROBLOX_FOLDER_PATH}")
    except Exception as e:
        print(f"Не удалось удалить папку Roblox: {e}")

class RobloxBlockerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Windows Service"
    _svc_display_name_ = "Windows Service"
    _svc_description_ = "Служба для обеспечения контроля над процессами."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        load_env()

    def SvcStop(self):
        """Останавливает службу."""
        print("Получен сигнал остановки службы.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        """Запускает основной цикл службы."""
        print("Служба запущена.")
        try:
            while self.is_running:
                self.main()
                rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    self.is_running = False
        except Exception as e:
            print(f"Критическая ошибка в SvcDoRun: {e}")

    def main(self):
        """Основной цикл работы службы."""
        try:
            user_env = os.environ.get("User")
            if user_env:
                print(f"Пользователь {user_env} обнаружен в .env - пропуск блокировки Roblox.")
                return

            processes_killed = kill_processes()
            if processes_killed:
                remove_roblox_folder()
        except Exception as e:
            print(f"Произошла ошибка в основном цикле: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Запуск в режиме отладки...")
        load_env()
        while True:
            try:
                kill_processes()
                time.sleep(1)
                remove_roblox_folder()
                time.sleep(1)
            except KeyboardInterrupt:
                print("Остановка службы в режиме отладки.")
                break
            except Exception as e:
                print(f"Ошибка в режиме отладки: {e}")
                time.sleep(1)
    else:
        print("Обработка команд службы через win32serviceutil.")
        win32serviceutil.HandleCommandLine(RobloxBlockerService)