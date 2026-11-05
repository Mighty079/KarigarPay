@echo off
netsh advfirewall firewall add rule name="Allow FastAPI Port 8000" dir=in action=allow protocol=TCP localport=8000
