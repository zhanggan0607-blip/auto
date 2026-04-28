# Pre-commit hook for bid-auto project (PowerShell version)
# This hook ensures TypeScript types are in sync with Django serializers

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running pre-commit checks..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Get the project root directory
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# ===========================================
# Step 1: Generate TypeScript types from Django serializers (Backend)
# ===========================================
Write-Host ""
Write-Host "Step 1: Generating TypeScript types from Django serializers..." -ForegroundColor Yellow

$BackendDir = Join-Path $ProjectRoot "backend"
Set-Location $BackendDir

$PythonExe = "C:\Users\ZhangGan\AppData\Local\Programs\Python\Python312\python.exe"

& $PythonExe -m scripts.generate_ts_types --apps tenders,enterprise,crawler,vectorlib,openclaw --output frontend/src/types/generated

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Failed to generate TypeScript types!" -ForegroundColor Red
    exit 1
}

Write-Host "TypeScript types generated successfully!" -ForegroundColor Green

# ===========================================
# Step 2: Run Frontend TypeScript type check
# ===========================================
Write-Host ""
Write-Host "Step 2: Running Frontend TypeScript type check..." -ForegroundColor Yellow

$FrontendDir = Join-Path $ProjectRoot "frontend"
Set-Location $FrontendDir

npx vue-tsc --noEmit --pretty

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Type check failed! Please fix type errors before committing." -ForegroundColor Red
    Write-Host ""
    Write-Host "Note: If you just added new Serializer fields, the types have been" -ForegroundColor Yellow
    Write-Host "auto-generated above. You may need to update your component code." -ForegroundColor Yellow
    exit 1
}

Write-Host "Frontend TypeScript type check passed!" -ForegroundColor Green

# ===========================================
# Step 3: Run ESLint check
# ===========================================
Write-Host ""
Write-Host "Step 3: Running ESLint..." -ForegroundColor Yellow

npx vue-cli-service lint --no-fix

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ESLint found issues. Please fix them or use 'git commit --no-verify' to bypass." -ForegroundColor Yellow
    exit 1
}

Write-Host "ESLint check passed!" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "All pre-commit checks passed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

exit 0