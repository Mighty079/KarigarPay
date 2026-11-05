@echo off
echo Installing updated, bug-fixed KarigarPay.apk on emulator...
"C:\Users\krish\AppData\Local\Android\Sdk\platform-tools\adb.exe" wait-for-device
"C:\Users\krish\AppData\Local\Android\Sdk\platform-tools\adb.exe" install -r "c:\Users\krish\Desktop\Projects\KarigarPay\frontend\KarigarPay.apk"
echo Launching KarigarPay app on screen...
"C:\Users\krish\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell am start -S -n com.karigarpay.neobank/.MainActivity
echo Success! App launched.
pause
