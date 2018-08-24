###############################################################################
##
## Description:
##  Test IPv4 / IPv6 performance of different RHELs in vSphere with netperf
##
###############################################################################
##
## Revision:
## v1.0 - boyang - 10/19/2018 - Build the script
##
###############################################################################


<#
.Synopsis
    Test IPv4 / IPv6 performance of different RHELs in vSphere with netperf

.Description
    Test IPv4 / IPv6 performance of different RHELs in vSphere with netperf

.Parameter vmName
    Name of the VM to add disk.

.Parameter hvServer
    Name of the ESXi server hosting the VM.

.Parameter testParams
    Test data for this test case
#>


param([String] $vmName, [String] $hvServer, [String] $testParams)


#
# Checking the input arguments
#
if (-not $vmName)
{
    "Error: VM name cannot be null!"
    exit
}

if (-not $hvServer)
{
    "Error: hvServer cannot be null!"
    exit
}

if (-not $testParams)
{
    Throw "Error: No test parameters specified"
}


#
# Display the test parameters so they are captured in the log file
#
"TestParams : '${testParams}'"


#
# Parse the test parameters
#
$rootDir = $null
$sshKey = $null
$ipv4 = $null


$params = $testParams.Split(";")
foreach ($p in $params)
{
    $fields = $p.Split("=")
    switch ($fields[0].Trim())
    {
    "sshKey"       { $sshKey = $fields[1].Trim() }
    "rootDir"      { $rootDir = $fields[1].Trim() }
    "ipv4"         { $ipv4 = $fields[1].Trim() }
    "TestLogDir"   { $testLogDir = $fields[1].Trim() }
    default        {}
    }
}

if (-not $rootDir)
{
    "Warn : no rootdir was specified"
}
else
{
    if ( (Test-Path -Path "${rootDir}") )
    {
        cd $rootDir
    }
    else
    {
        "Warn : rootdir '${rootDir}' does not exist"
        exit 100
    }
}

#
# Source the tcutils.ps1 file
#
. .\setupscripts\tcutils.ps1


PowerCLIImport
ConnectToVIServer $env:ENVVISIPADDR `
                  $env:ENVVISUSERNAME `
                  $env:ENVVISPASSWORD `
                  $env:ENVVISPROTOCOL


###############################################################################
#
# Main Body
#
###############################################################################
$retVal = $Failed


#
# The VM A and the VM B own the same part in names
#
$vmNameB = $vmName -replace "-A$","-B"
$vmObjectB = Get-VMHost -Name $hvServer | Get-VM -Name $vmNameB
Write-Host -F Gray "The VM B is $vmObjectB"
Write-Output "The VM B is $vmObjectB"
$ipv4B = ""


# Confirm the VM B power state
$vmObjectBPowerState = $vmObjectB.PowerState
Write-Host -F Gray "The VM B power state is $vmObjectBPowerState"
Write-Output "The VM B power state is $vmObjectBPowerState"
# Boot vmObjectB if its power state isn't PoweredOn and get its IP
if ($vmObjectBPowerState -ne "PoweredOn")
{
    Write-Host -F Gray "Start to power on VM $vmObjectB"
    Write-Output "Start to power on VM $vmObjectB"
    $vmObjectBOn = Start-VM -VM $vmObjectB -Confirm:$False
    $timeout = 360
    while ($timeout -gt 0)
    {
        $vmObjectB = Get-VMHost -Name $hvServer | Get-VM -Name $vmNameB
        $vmTempPowerState = $vmObjectB.PowerState
        Write-Host -F Gray "The VM B power state is $vmTempPowerState"
        Write-Output "The VM B power state is $vmTempPowerState"
        if ($vmTempPowerState -eq "PoweredOn")
        {
            $ipv4B = GetIPv4 $vmNameB $hvServer
            Write-Host -F Gray "The VM B ipv4 is $ipv4B"
            Write-Output "The VM B ipv4 is $ipv4B"
            if ($ipv4B -ne $null)
            {
                break
            }
        }
        Start-Sleep -S 6
        $timeout = $timeout - 6
        if ($timeout -eq 0)
        {
            Write-Host -F Yellow "WARNING: Timeout, and power off the VM B"
            Write-Output "WARNING: Timeout, and power off the VM B"
            $vmObjectBOff = Stop-VM -VM $vmObjectB -Confirm:$False
            return $Aborted
        }
    }
}
# If its power state is PoweredOn, get its IP
else
{
    $ipv4B = GetIPv4 $vmNameB $hvServer
    Write-Host -F Gray "The VM B ipv4 is $ipv4B"
    Write-Output "The VM B ipv4 is $ipv4B"
    if ($ipv4B -eq $null)
    {
        Write-Host -F Yellow "WARNING: can't get VMB's ipv4, abort. And powered off the VM B"
        Write-Output "WARNING: can't get VMB's ipv4, abort. And powered off the VM B"
        $vmObjectBOff = Stop-VM -VM $vmObjectB -Confirm:$False
        return $Aborted
    }
}


# Send netperf_server.py to VM B
.\bin\pscp -q -i ssh\${sshKey} \remote-scripts\netperf_server.py root@${ipv4}:/root/

# Execute the script in VM B
$ret = SendCommandToVM $ipv4B $sshKey "cd /root && dos2unix netperf_server.py && chmod u+x netperf_server.py && python netperf_server.py"
if (-not $ret)
{
	Write-Host -F Red "FAIL: Failed to execute netperf_server.py in VM"
	Write-Output "FAIL: Failed to execute netperf_server.py in VM"
	DisconnectWithVIServer
	Write-Host -F Red "Last, power off the VM B"
    Write-Output "Last, power off the VM B"
    $vmObjectB = Get-VMHost -Name $hvServer | Get-VM -Name $vmNameB
    $vmObjectBOff = Stop-VM -VM $vmObjectB -Confirm:$False
	return $Aborted
}
else
{
	Write-Host -F Green "PASS: Execute script in VM successfully"
	Write-Output "PASS: Execute script in VM successfully"
}


# Execute the script in VM A
$ret = SendCommandToVM $ipv4B $sshKey "cd /root && dos2unix netperf_client.py && chmod u+x netperf_client.py && python netperf_client.py"
if (-not $ret)
{
	Write-Host -F Red "FAIL: Failed to execute netperf_client.py in VM"
	Write-Output "FAIL: Failed to execute netperf_client.py in VM"
	return $Aborted
}
else
{
	Write-Host -F Green "PASS: Execute script in VM successfully
	Write-Output "PASS: Execute script in VM successfully"
	$retVal = $Passed
}


DisconnectWithVIServer
return $retVal
