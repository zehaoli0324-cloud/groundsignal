Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
scriptPath = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "launch-collector.pyw")
On Error Resume Next
shell.Run "pythonw.exe " & Chr(34) & scriptPath & Chr(34), 0, False
If Err.Number <> 0 Then
    MsgBox "Unable to start Python. Open launch-collector.pyw with Python, or install Python and add it to PATH.", 16, "GroundSignal"
End If
