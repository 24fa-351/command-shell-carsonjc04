import os
import subprocess
import shlex
import re

def execute_command(command):
    # Substitute environment variables in the command
    command = substitute_env_vars(command)

    # Handle built-in commands
    if command.startswith("cd "):
        path = command[3:].trip()
        try:
            os.chdir(path)
        except FileNotFoundError:
            print(f"cd: No such file or directory: {path}")
    elif command == "pwd":
        print(os.getcwd())
    elif command.startswith("set "):
        parts = command.split(maxsplit=2)
        if len(parts) == 3:
            os.environ[parts[1]] = parts[2]
        else:
            print("Usage: set <variable> <value>")
    elif command.startswith("unset "):
        var = command.split(maxsplit=1)[1]
        os.environ.pop(var, None)
    elif command.startswith("echo "):
        parts = command.split(maxsplit=1)
        output = substitute_env_vars(parts[1]) if len(parts) > 1 else ""
        print(output)
    else:
        # Handle complex commands (piping, redirection, background execution)
        handle_complex_command(command)

def substitute_env_vars(command):
    """Replace $VAR with its value in the command."""
    pattern = re.compile(r'\$(\w+)')
    matches = pattern.findall(command)
    for var in matches:
        value = os.environ.get(var, '')
        command = command.replace(f"${var}", value)
    return command

def handle_complex_command(command):
    """Handle piping, redirection, and background execution."""
    if "|" in command:
        handle_piping(command)
    elif ">" in command or "<" in command:
        handle_redirection(command)
    elif command.endswith("&"):
        handle_background_execution(command[:-1].strip())
    else:
        run_command(command)

def handle_piping(command):
    """Handle commands separated by pipes."""
    commands = [shlex.split(cmd.strip()) for cmd in command.split("|")]
    prev_process = None
    for i, cmd in enumerate(commands):
        stdin = prev_process.stdout if prev_process else None
        stdout = subprocess.PIPE if i < len(commands) - 1 else None
        prev_process = subprocess.Popen(cmd, stdin=stdin, stdout=stdout)
    if prev_process:
        prev_process.communicate()

def handle_redirection(command):
    """Handle input/output redirection."""
    parts = shlex.split(command)
    cmd = []
    input_file = None
    output_file = None
    append = False

    i = 0
    while i < len(parts):
        if parts[i] == '>':
            output_file = parts[i + 1]
            i += 1
        elif parts[i] == '>>':
            output_file = parts[i + 1]
            append = True
            i += 1
        elif parts[i] == '<':
            input_file = parts[i + 1]
            i += 1
        else:
            cmd.append(parts[i])
        i += 1

    stdin = open(input_file, 'r') if input_file else None
    stdout = open(output_file, 'a' if append else 'w') if output_file else None

    subprocess.run(cmd, stdin=stdin, stdout=stdout)

    if stdin:
        stdin.close()
    if stdout:
        stdout.close()

def handle_background_execution(command):
    """Run a command in the background."""
    subprocess.Popen(shlex.split(command))

def run_command(command):
    """Run a single external command."""
    try:
        subprocess.run(shlex.split(command), check=True)
    except FileNotFoundError:
        print(f"{command.split()[0]}: command not found")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def main():
    while True:
        try:
            command = input("xsh# ").strip()
            if command in {"quit", "exit"}:
                print("Exiting xsh...")
                break
            execute_command(command)
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
