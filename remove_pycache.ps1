<#
.SYNOPSIS
  Removes all __pycache__ directories from the current directory, recursively.

.DESCRIPTION
  Recursively searches from the current directory downward
  and deletes all Python __pycache__ folders.

.EXAMPLE
  ./remove_pycache.ps1
#>

Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
