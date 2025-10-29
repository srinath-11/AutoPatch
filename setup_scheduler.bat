@echo off
echo Setting up Windows Task Scheduler for AutoPatch...

:: Create scheduled task to run daily at 2 AM
schtasks /create /tn "AutoPatch-Updater" /tr "C:\Users\moham\Projects\Linux project\AutoPatch\autopatch.bat" /sc daily /st 02:00 /ru SYSTEM

echo.
echo Scheduled task created!
echo Task Name: AutoPatch-Updater
echo Schedule: Daily at 2:00 AM
echo.
echo To view the task: schtasks /query /tn "AutoPatch-Updater"
echo To delete the task: schtasks /delete /tn "AutoPatch-Updater"
pause