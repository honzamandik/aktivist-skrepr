param(
    [string]$venvName = "venv"
)

Write-Host "Creating virtual environment: $venvName"
python -m venv $venvName
Write-Host "Activating virtual environment"
. "$venvName\Scripts\Activate.ps1"
Write-Host "Installing requirements"
pip install -r requirements.txt
Write-Host "Done. Run 'Deactivate' to exit the venv." 
