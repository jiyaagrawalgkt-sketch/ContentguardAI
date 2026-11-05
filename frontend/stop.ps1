# Forwarder to root stop.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir
& (Join-Path $RootDir "stop.ps1") @args
