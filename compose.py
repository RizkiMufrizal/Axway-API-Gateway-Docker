#!/usr/bin/env python2.7
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src/core/src"))

print sys.path
	
from src.compose.src.compose import main

# Unbuffered sysout
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

main()