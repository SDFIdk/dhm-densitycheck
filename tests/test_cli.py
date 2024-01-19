import subprocess

def test_cli_help():
    subprocess.check_call(['point_density', '-h'])
