#!/usr/bin/env python3

import sys

def main():
    print(f"Hello, {sys.argv[1] if len(sys.argv) > 1 else 'World'}!")

if __name__ == "__main__":
    sys.exit(main())