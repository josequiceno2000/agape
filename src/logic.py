import argparse

def generate_message(name, formal=False):
    greeting = "Greetings" if formal else "Hello"
    return f"{greeting}, {name}!"

def main(argv=None):
    parser = argparse.ArgumentParser(description="Agape CLI Tool")
    parser.add_argument("name", nargs="?", default="World")
    parser.add_argument("--formal", action="store_true")
    args = parser.parse_args(argv)
    
    print(generate_message(args.name, args.formal))
    return 0