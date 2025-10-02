Get-ChildItem -Path . -Recurse -Include *.pyc | Remove-Item -Force
Get-ChildItem -Path . -Recurse -Include __pycache__ | Remove-Item -Recurse -Force
Write-Host "Cache de arquivos .pyc e pastas __pycache__ limpo!"