import subprocess

class sequance():
    def __init__(self, COM=None):
        self.COM = COM

    def program(self, currentPath, programFile):
        p = subprocess.run([currentPath + '\\SFU\\sfu.exe', 'upgrade', self.COM, programFile], 
                   shell=True,
                   stdout=subprocess.PIPE, 
                   stderr=subprocess.PIPE, 
                   universal_newlines=True)
        output = p.stdout

        if "upgrade done with success" in output:
            print(f"{self.COM} finish modem update")
            return True
        else:
            print(f"{self.COM} failed to update modem")
            return False