# Forwarder to root start.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir
& (Join-Path $RootDir "start.ps1") @args
