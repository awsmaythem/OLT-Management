import paramiko
import time

def login_to_olt(host, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=int(port), username=username, password=password)
    
    tn = client.invoke_shell()
    time.sleep(1)
    tn.send('enable\n')
    time.sleep(1)
    tn.send('config\n')
    time.sleep(1)
    return tn

def execute_command(tn, command):
    tn.send(command + "\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print(output)
    return output

def save_configuration(tn):
    tn.send("save\n")
    time.sleep(1)
    output = tn.recv(65535).decode('ascii')
    print(output)
    
    if "{ <cr>|configuration<K>|data<K> }:" in output:
        tn.send("\n")  # or "data\n" if that's what you want to save
        time.sleep(1)
        output = tn.recv(65535).decode('ascii')
        print(output)

    end_time = time.time() + 86  # Set the timeout for 86 seconds
    while time.time() < end_time:
        if "The data of" in output and "board is saved" in output:
            print("Configuration has been saved successfully.")
            return
        time.sleep(5)  # Wait for 5 seconds before checking again
        output = tn.recv(65535).decode('ascii')
        print(output)

    print("Save operation timed out.")

def add_ont(tn):
    tn.send("display ont autofind all\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print("Output of the 'display ont autofind all' command:")
    print(output)

    if "Failure: The automatically found ONTs do not exist" in output:
        print("No ONTs found. Exiting the session.")
        return

    slot_value = input("Enter the SLOT field value: ")
    pon_value = input("Enter the PON field value: ")
    id_value = input("Enter the SERIAL ID field value: ")

    execute_command(tn, f"interface gpon 0/{slot_value}")
    time.sleep(3)
    tn.send(f"ont add {pon_value} sn-auth {id_value} omci ont-lineprofile-id 1 ont-srvprofile-id 1\n")
    tn.send("\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print(f"Output of the 'ont add {pon_value} sn-auth {id_value} omci ont-lineprofile-id 1 ont-srvprofile-id 1' command:")
    print(output)

    onu_value = input("Enter the ONU ID field value: ")
    execute_command(tn, "quit")
    execute_command(tn, f"service-port vlan 9 gpon 0/{slot_value}/{pon_value} ont {onu_value} gemport 1 multi-service user-vlan 9")
    tn.send("\n")
    time.sleep(3)
    execute_command(tn, f"service-port vlan 10 gpon 0/{slot_value}/{pon_value} ont {onu_value} gemport 2 multi-service user-vlan 10")
    tn.send("\n")
    time.sleep(3)
    # Save the configuration
    save_configuration(tn)

def delete_ont(tn):
    tn.send("display ont autofind all\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print("Output of the 'display ont autofind all' command:")
    print(output)

    id_value = input("Enter the SERIAL ID field value: ")
    tn.send(f"display ont info by-sn {id_value}\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print("Output of the 'display ont info by-sn' command:")
    print(output)
    tn.send("Q")
    slot_value = input("Enter the SLOT field value: ")
    pon_value = input("Enter the PON field value: ")
    onu_value2 = input("Enter the ONU ID field value: ")

    tn.send(f"display service-port port 0/{slot_value}/{pon_value} ont {onu_value2}\n")
    tn.send("\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print(f"Output of the 'display service-port port 0/{slot_value}/{pon_value} ont {onu_value2}' command:")
    print(output)

    id_undo_values = input("Enter the UNDO ID field values separated by commas (e.g., 1,2,3,4): ").split(',')
    for id_undo_value in id_undo_values:
        tn.send(f"undo service-port {id_undo_value.strip()}\n")
        time.sleep(1)
        tn.send("\n")

    execute_command(tn, f"interface gpon 0/{slot_value}")
    execute_command(tn, f"ont delete {pon_value} {onu_value2}")
    execute_command(tn, "quit")
    # Save the configuration
    save_configuration(tn)

def main():
    host = "IP-address"
    port = "22"  # Default port for SSH is 22
    username = "root"
    password = "password"

    tn = login_to_olt(host, port, username, password)
    
    while True:
        action = input("Do you want to add or delete an ONT? (add/delete/exit): ").strip().lower()
        if action == "exit":
            tn.close()
            break
        if action == "add":
            add_ont(tn)
        elif action == "delete":
            delete_ont(tn)
        else:
            print("Invalid option. Please enter 'add' or 'delete'.")

if __name__ == "__main__":
    main()
