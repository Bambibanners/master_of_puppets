# Master of Puppets - Node Bootstrap (Podman)
param(
    [string]$ServerUrl = "https://localhost:8001",
    [string]$JoinToken,
    [int]$Count = 1
)

Write-Host "Bootstrapping Environment Node (Podman) x$Count..." -ForegroundColor Cyan

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Error "Podman is not installed."
    exit 1
}

if (-not $JoinToken) {
    $JoinToken = Read-Host "Enter Join Token"
}

# 1. Parse Token (Token-Embedded Trust)
Write-Host "Parsing Secure Token..."
try {
    # Base64 Decode
    $JsonBytes = [System.Convert]::FromBase64String($JoinToken)
    $JsonStr = [System.Text.Encoding]::UTF8.GetString($JsonBytes)
    $Payload = $JsonStr | ConvertFrom-Json
    
    $RealToken = $Payload.t
    $CaContent = $Payload.ca
    
    # Save CA to disk
    $CaContent = $CaContent -replace "`r`n", "`n"
    $CaContent = $CaContent -replace "`n", "`n" 
    $CaContent = $CaContent.Trim() + "`n"
    
    [System.IO.File]::WriteAllText("bootstrap_ca.crt", $CaContent, [System.Text.Encoding]::ASCII)
    Write-Host "Trust Root extracted." -ForegroundColor Green
}
catch {
    Write-Error "Invalid Token Format. Ensure you are using a v0.8+ Token."
    exit 1
}

# 1.5 Setup Managed Network Mounts (Host-Passthrough)
Write-Host "Fetching Network Mount Config..." -ForegroundColor Cyan

# Fetch Config from Server using Extracted Token
$ConfigUri = "$ServerUrl/config/mounts"
$MountsJson = curl.exe -k -s -H "X-Join-Token: $RealToken" $ConfigUri

try {
    if ($MountsJson) {
        $MountArr = $MountsJson | ConvertFrom-Json
        
        if ($MountArr.Count -gt 0) {
            # Ensure Podman Machine is running
            podman machine start | Out-Null
            
            foreach ($Mount in $MountArr) {
                $Name = $Mount.name
                $Path = $Mount.path
                
                # 1. Verify Host Access
                if (-not (Test-Path $Path)) {
                    Write-Warning "⚠️  Host cannot access: [$Name] -> [$Path]. Skipping..."
                    continue
                }
                
                # 2. Derive Internal Linux Path (Standardized)
                # /mnt/mop/[name]
                $LinuxMountPoint = "/mnt/mop/$Name"
                
                Write-Host "   Mapping [$Name] -> [$LinuxMountPoint]"
                
                # 3. Mount in VM
                podman machine ssh "sudo mkdir -p $LinuxMountPoint"
                
                # Clean up existing if needed ?? (mount over it is fine usually)
                podman machine ssh "sudo mount -t drvfs '$Path' '$LinuxMountPoint'" 2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "   ✅ Mounted." -ForegroundColor DarkGreen
                }
                else {
                    Write-Warning "   ⚠️  Mount attempted (check logs if failed)."
                }
            }
        }
    }
}
catch {
    Write-Warning "Failed to process network mounts config. Proceeding without specific mounts."
}

# 2. Download Configuration
Write-Host "Fetching configuration from Hub (Secure)..."
$Uri = "$ServerUrl/api/node/compose?token=$JoinToken"

# Secure Download using extracted CA
# --ssl-no-revoke: Required on Windows because the internal CA has no CRL/OCSP
# FALLBACK: Using -k due to persistent Schannel PEM parsing issues. 
# The Python Node will enforce mTLS strictly.
curl.exe -k --ssl-no-revoke -o "node-compose.yaml" $Uri

if ($LASTEXITCODE -ne 0 -or -not (Test-Path "node-compose.yaml")) {
    Write-Error "Failed to download configuration. (Exit Code: $LASTEXITCODE)"
    exit 1
}

# 2. Start
Write-Host "Starting Node..."

# Ensure podman-compose is in path (User Install Location)
$env:Path = "$env:Path;C:\Users\thoma\AppData\Roaming\Python\Python312\Scripts"

if (-not (Get-Command podman-compose -ErrorAction SilentlyContinue)) {
    Write-Error "podman-compose found. Please install it: pip install podman-compose"
    exit 1
}

podman-compose -f node-compose.yaml up -d --scale node=$Count

Write-Host "Node Started!" -ForegroundColor Green
