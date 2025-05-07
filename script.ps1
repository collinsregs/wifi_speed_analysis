# Hourly Speedtest Data Collection Script

# Define the path to the speedtest script
$scriptPath = "./speedtest"
$scriptArguments = "-f", "csv"

# Get the current date in YYYY-MM-DD format for the filename
$currentDate = Get-Date -Format "yyyy-MM-dd"
$outputPath = "data/speedtest_results_$currentDate.csv"
$logPath = "logs/speedtest_log_$currentDate.txt"

# Create the logs directory if it doesn't exist
if (-not (Test-Path -Path "logs" -PathType Container)) {
    New-Item -Path "logs" -ItemType Directory | Out-Null
}

# Create the data directory if it doesn't exist
if (-not (Test-Path -Path "data" -PathType Container)) {
    New-Item -Path "data" -ItemType Directory | Out-Null
}

# Function to write to log file
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logPath -Append
}

# Function to run a single speedtest and append results
function Test-SpeedTest {
    # Get the current timestamp
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Log start of test
    Write-Log "Starting speedtest"
    
    # Run the speedtest and capture its output
    $scriptOutput = & $scriptPath @scriptArguments
    
    if ($scriptOutput) {
        # Define the headers for the speedtest CSV output
        $headers = "Server Name", "Server ID", "Latency", "Jitter", "Packet Loss", "Download", "Upload", 
                   "Download Bytes", "Upload Bytes", "Share URL", "Download Server Count", "Download Latency", 
                   "Download Latency Jitter", "Download Latency Low", "Download Latency High", "Upload Latency", 
                   "Upload Latency Jitter", "Upload Latency Low", "Upload Latency High", "Idle Latency"
        
        try {
            # Convert the CSV string output to a PowerShell object with proper headers
            $csvData = $scriptOutput | ConvertFrom-Csv -Header $headers
            
            if ($csvData) {
                # Add the timestamp property
                $csvData | Add-Member -MemberType NoteProperty -Name "Timestamp" -Value $timestamp
                
                # Create the file with headers if it doesn't exist
                if (-not (Test-Path $outputPath)) {
                    $csvData | Export-Csv -Path $outputPath -NoTypeInformation
                    Write-Log "Created new file: $outputPath"
                } else {
                    # Append to the existing file without the header
                    $csvData | Export-Csv -Path "temp.csv" -NoTypeInformation
                    Get-Content "temp.csv" | Select-Object -Skip 1 | Add-Content -Path $outputPath
                    Remove-Item -Path "temp.csv"
                    Write-Log "Appended to existing file: $outputPath"
                }
                
            } else {
                Write-Log "The script produced CSV output, but it couldn't be converted to objects."
            }
        } catch {
            $errorMessage = $_.Exception.Message
            Write-Log "Error converting script output to CSV: $errorMessage"
            Write-Log "Raw script output: $scriptOutput"
        }
    } else {
        Write-Log "The script '$scriptPath' produced no output."
    }
}

# Create log file if it doesn't exist
if (-not (Test-Path $logPath)) {
    "Log created on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $logPath
}

# Run the speedtest
Test-SpeedTest


# to schedule in powershell run the command
# Register-ScheduledJob -Name "HourlySpeedTest" -ScriptBlock { Set-Location -Path "path_to project" .\script.ps1 } -Trigger (New-JobTrigger -Once -At "00:00" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)) -ScheduledJobOption (New-ScheduledJobOption -RunElevated)