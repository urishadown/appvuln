#! usr/bin/env python3
import os
import subprocess

comando = input("Digite um comando: ")

os.system(comando)

subprocess.run(comando, shell=True)
