import os
import sys
import time
import psutil
import servicemanager
import win32serviceutil
import win32service
import win32event
import subprocess
import logging

# Настройка логирования
logging.basicConfig(
    filename="roblox_blocker_service.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
        logging.info(f"Загрузка переменных из {filepath}")
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
                    logging.info(f'Установлена переменная: {key}={value}')
    else:
        logging.info("Файл .env не найден. Переменные не загружены.")

def kill_processes():
    """Завершает процессы, связанные с Roblox."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            process_name = proc.info['name']
            if process_name and any(keyword.lower() in process_name.lower() for keyword in BLOCKED_PROCESSES):
                logging.info(f"Завершение процесса {process_name} (PID: {proc.info['pid']})...")
                subprocess.run(["taskkill", "/PID", str(proc.info['pid']), "/F"], check=True)
    except Exception as e:
        logging.error(f"Ошибка при завершении процесса: {e}")

def remove_roblox_folder():
    """Находит и удаляет папку Roblox в AppData."""
    try:
        if os.path.exists(ROBLOX_FOLDER_PATH):
            logging.info(f"Удаление папки Roblox: {ROBLOX_FOLDER_PATH}")
            # Рекурсивное удаление папки
            for root, dirs, files in os.walk(ROBLOX_FOLDER_PATH, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    os.chmod(file_path, 0o777)  # Снять атрибуты только для чтения
                    os.remove(file_path)
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    os.chmod(dir_path, 0o777)  # Снять атрибуты только для чтения
                    os.rmdir(dir_path)
            os.rmdir(ROBLOX_FOLDER_PATH)
        else:
            logging.info(f"Папка Roblox не найдена: {ROBLOX_FOLDER_PATH}")
    except Exception as e:
        logging.error(f"Не удалось удалить папку Roblox: {e}")

class RobloxBlockerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WindowsService"
    _svc_display_name_ = "Roblox Blocker Service"
    _svc_description_ = "Служба для блокировки процессов Roblox и удаления папки Roblox."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        # Загружаем переменные из .env при старте службы
        load_env()

    def SvcStop(self):
        """Останавливает службу."""
        logging.info("Получен сигнал остановки службы.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        """Запускает основной цикл службы."""
        logging.info("Служба запущена.")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        try:
            while self.is_running:
                self.main()
                # Проверка сигнала остановки каждую секунду
                rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    self.is_running = False
        except Exception as e:
            logging.error(f"Критическая ошибка в SvcDoRun: {e}")

    def main(self):
        """
        Основной цикл работы службы.
        Если задана переменная окружения User (любого значения), блокировка Roblox не выполняется.
        """
        try:
            user_env = os.environ.get("User")
            if user_env:
                logging.info(f"Пользователь {user_env} обнаружен в .env - пропуск блокировки Roblox.")
                return

            kill_processes()
            remove_roblox_folder()
        except Exception as e:
            logging.error(f"Произошла ошибка в основном цикле: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Запуск в режиме отладки...")
        logging.info("Запуск службы в режиме отладки.")
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RobloxBlockerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Обработка команд (install, start, stop, remove)
        logging.info("Обработка команд службы через win32serviceutil.")
        win32serviceutil.HandleCommandLine(RobloxBlockerService)
