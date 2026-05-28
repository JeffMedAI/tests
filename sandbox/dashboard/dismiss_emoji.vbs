Set objShell = CreateObject("WScript.Shell")
objShell.AppActivate "Emoji and more"
WScript.Sleep 300
objShell.SendKeys "{ESC}"
WScript.Sleep 200
objShell.SendKeys "{ESC}"
