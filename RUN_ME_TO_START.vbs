Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = "python"

If fso.FileExists(scriptDir & "\.venv\Scripts\python.exe") Then
    pythonExe = Chr(34) & scriptDir & "\.venv\Scripts\python.exe" & Chr(34)
End If

installCommand = "cmd /c cd /d " & Chr(34) & scriptDir & Chr(34) & _
    " && " & pythonExe & " -m pip install -r requirements.txt"

installExitCode = shell.Run(installCommand, 1, True)

If installExitCode <> 0 Then
    MsgBox "Requirements install failed. See the console window for details.", vbExclamation, "Launch failed"
    WScript.Quit installExitCode
End If

runCommand = "cmd /c cd /d " & Chr(34) & scriptDir & Chr(34) & _
    " && " & pythonExe & " main.py"

shell.Run runCommand, 0, False
