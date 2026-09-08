@echo off
chcp 65001 >nul
set PYTHONDONTWRITEBYTECODE=1
if "%1" == "" (
	cls
	echo 提示: 请将需要处理的 HTML 文件拖放到此批处理文件上。
	echo 目标 HTML 文件需要先使用 SingleFile 浏览器扩展保存。
	echo 本程序使用 Aria2c、Python 及相关库：requests、subprocess、splitext、BeautifulSoup、pandas
	echo ----------
	echo 使用方法：将 HTML 文件拖放到此批处理文件上开始处理。
	echo 如需同时处理多个文件，请运行 bp1688html.bat。
	echo 请提前安装上述必要程序和扩展。
	pause >nul
) else (
	@echo y|Cacls %* /c /t /p Everyone:f 2>nul
	if not exist "%~n1" (
		mkdir "%~n1"
		cd "%~n1"
		python ..\main.py "%~f1"
	) else (
		if exist "%~n1\rebuild.bat" (
			cd "%~n1"
			call rebuild.bat
		) else (
			cd "%~n1"
			python ..\main.py "%~f1"
		)
	)
	@echo [DEFAULT]>>#URL.url
	@echo BASEURL=https://detail.1688.com/offer/%~n1.html>>#URL.url
	@echo [InternetShortcut]>>#URL.url
	@echo URL=https://detail.1688.com/offer/%~n1.html>>#URL.url
	@echo IconIndex=41>>#URL.url
	@echo IconFile=C:\WINDOWS\system32\shell32.dll>>#URL.url
	set var=处理完成，倒计时
	for /l %%i in (2,-1,1) do (  
	@echo %var% %%i ...
	ping -n 2 127.1>nul
	)
	cd ..
)
