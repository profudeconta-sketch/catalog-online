# Lansare manuală, exclusiv locală, a laboratorului Neluțu.
# Nu instalează pachete, nu accesează date școlare și nu publică pe internet.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Laborator experimental Neluțu — doar localhost." -ForegroundColor Yellow
Write-Host "NU introduceți nume de elevi, parole, documente sau date reale."
Write-Host "Oprire: Ctrl+C. Aplicația activă nu este modificată."
$oldFlag = [Environment]::GetEnvironmentVariable("NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL", "Process")
try {
    python -c "import streamlit; print('Streamlit disponibil:', streamlit.__version__)"
    if ($LASTEXITCODE -ne 0) { throw "Streamlit nu este instalat. Consultați NELUTU_LABORATOR_TESTARE.md." }
    $env:NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL = "1"
    python -m streamlit run nelutu_dialogue_preview.py --server.address localhost --server.headless true
    if ($LASTEXITCODE -ne 0) { throw "Laboratorul s-a oprit cu o eroare." }
}
finally {
    [Environment]::SetEnvironmentVariable("NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL", $oldFlag, "Process")
    Write-Host "Indicatorul experimental a fost restabilit."
}
