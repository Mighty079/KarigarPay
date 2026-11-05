@echo off
echo Starting Android Emulator (Pixel_6) with DNS routing...
cd /d "C:\Users\krish\AppData\Local\Android\Sdk\emulator"
emulator.exe -avd Pixel_6 -dns-server 8.8.8.8,1.1.1.1,192.168.1.1 -no-snapshot-load -no-boot-anim
