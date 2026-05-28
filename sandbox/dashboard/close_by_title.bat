@echo off
powershell -Command "Get-Process | Where-Object {$_.MainWindowTitle -like '*Emoji*'} | Stop-Process -Force"
powershell -Command "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class Win { [DllImport(\"user32.dll\")] public static extern IntPtr FindWindow(string c, string t); [DllImport(\"user32.dll\")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l); }'; $h = [Win]::FindWindow($null, 'Emoji and more'); if ($h -ne [IntPtr]::Zero) { [Win]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) }"
exit
