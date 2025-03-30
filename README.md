# antiRoblox  
Данный проект предназначен для автоматического удаления игры Roblox и завершения действующих процессов игры в системе   

# Использование
1. Клонировать репозиторий:  
```git clone https://github.com/Processori7/antiRoblox.git```
2. Перейти в папку (на Windows):  
```cd /d antiRoblox```  
Unix:  
```cd antiRoblox```  
3. Создать виртуальное окружение:  
```python -m venv venv```  
На Unix: ```python3 -m venv venv```  
4. Активировать виртуальное окружение:  
. На Windows:  
```venv\Scripts\activate```  
. Unix:  
```source venv/bin/activate```
5. Установить зависимости:
```pip install -r requirements.txt```
6. Запустить файл:
```python Windows Service.py```  

## Установка в качестве службы (требуются права администратора)  
Запуск и установка:  
```sc create Windows Service binPath= "путь к Windows Service.exe" start= auto```  
```sc start Windows Service```  
Удаление:
```sc stop Windows Service```
```sc delete Windows Service```  
И удалить файла.  

## Сборка  
Использовать auto-py-to-exe, чтобы собрать в exe файл. Выставить параметры:  
onefile  
windowed - скрывает консоль  
В Additional files добавить папки:  
pywin32_system32/  
pythonwin/  
psutil/  
win32ctypes/  
win32comext/  
win32/  
win32com/  
В hidden imports: win32timezone