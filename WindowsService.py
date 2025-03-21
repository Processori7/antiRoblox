import os
import time
import psutil

# Настройки
BLOCKED_PROCESSES = [
    "RobloxPlayerInstaller.exe",
    "RobloxStudioInstaller.exe",
    "RobloxPlayerBeta.exe",
    "RobloxCrashHandler.exe"
]

# Путь к папке Roblox
ROBLOX_FOLDER_PATH = os.path.join(os.getenv("LOCALAPPDATA"), "Roblox")

def kill_processes():
    """Завершает процессы, связанные с Roblox."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            process_name = proc.info['name'].lower()
            if any(keyword.lower() in process_name for keyword in ["roblox", "Roblox"]):
                proc.kill()
                print(f"[INFO] Процесс {proc.info['name']} (PID: {proc.info['pid']}) завершен.")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"[ERROR] Ошибка при завершении процесса: {e}")

def remove_roblox_folder():
    """Находит и удаляет папку Roblox в AppData."""
    try:
        if os.path.exists(ROBLOX_FOLDER_PATH):
            # Удаление папки рекурсивно
            for root, dirs, files in os.walk(ROBLOX_FOLDER_PATH, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    os.chmod(file_path, 0o777)  # Снимаем атрибуты только для чтения
                    os.remove(file_path)
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    os.chmod(dir_path, 0o777)  # Снимаем атрибуты только для чтения
                    os.rmdir(dir_path)
            os.rmdir(ROBLOX_FOLDER_PATH)
            print(f"[INFO] Папка Roblox удалена: {ROBLOX_FOLDER_PATH}")
        else:
            print(f"[INFO] Папка Roblox не найдена: {ROBLOX_FOLDER_PATH}")
    except Exception as e:
        print(f"[ERROR] Не удалось удалить папку Roblox: {e}")

def run_monitoring():
    """Запускает мониторинг процессов и папки."""
    while True:
        kill_processes()
        remove_roblox_folder()
        time.sleep(1)  # Проверяем каждую секунду

if __name__ == "__main__":
    try:
        print("[INFO] Скрипт запущен.")
        run_monitoring()
    except KeyboardInterrupt:
        print("\n[INFO] Скрипт остановлен пользователем.")