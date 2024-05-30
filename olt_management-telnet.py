import telnetlib
import time

def login_to_olt(host, port, username, password):
    tn = telnetlib.Telnet(host, port)
    time.sleep(1)
    tn.write(username.encode('ascii') + b"\n")
    time.sleep(1)
    tn.write(password.encode('ascii') + b"\n")
    time.sleep(1)
    tn.write(b"enable\n")
    time.sleep(1)
    tn.write(b"config\n")
    time.sleep(1)
    return tn

def execute_command(tn, command):
    tn.write(command.encode('ascii') + b"\n")
    time.sleep(3)
    output = tn.read_very_eager().decode('ascii')
    print(output)
    return output

def save_configuration(tn):
    tn.write("save\n")
    time.sleep(1)
    output = tn.recv(65535).decode('ascii')
    print(output)
    
    if "{ <cr>|configuration<K>|data<K> }:" in output:
        tn.write("\n")  # or "data\n" if that's what you want to save
        time.sleep(1)
        output = tn.recv(65535).decode('ascii')
        print(output)
    
    while True:
        time.sleep(3)  # Adjust sleep duration as necessary
        output = tn.recv(65535).decode('ascii')
        print(output)
        
        # Check for the completion message
        if "The data of" in output and "is saved completely" in output:
            break
    print("Configuration has been saved successfully.")

def add_ont(tn):
    tn.write(b"display ont autofind all\n")
    time.sleep(3)
    output = tn.read_very_eager().decode('ascii')
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
    tn.write(f"ont add {pon_value} sn-auth {id_value} omci ont-lineprofile-id 1 ont-srvprofile-id 1\n")
    tn.write("\n")
    time.sleep(3)
    output = tn.recv(65535).decode('ascii')
    print("Output of the 'ont add {pon_value} sn-auth {id_value} omci ont-lineprofile-id 1 ont-srvprofile-id 1' command:")
    print(output)

    onu_value = input("Enter the ONU ID field value: ")
    execute_command(tn, "quit")
    execute_command(tn, f"service-port vlan 9 gpon 0/{slot_value}/{pon_value} ont {onu_value} gemport 1 multi-service user-vlan 9\n")
    tn.write("\n")
    time.sleep(3)
    execute_command(tn, f"service-port vlan 10 gpon 0/{slot_value}/{pon_value} ont {onu_value} gemport 2 multi-service user-vlan 10\n")
    tn.write("\n")
    time.sleep(3)
    # Save the configuration
    save_configuration(tn)

def delete_ont(tn):
    tn.write(b"display ont autofind all\n")
    time.sleep(3)
    output = tn.read_very_eager().decode('ascii')
    print("Output of the 'display ont autofind all' command:")
    print(output)

    id_value = input("Enter the SERIAL ID field value: ")
    tn.write(f"display ont info by-sn {id_value}\n".encode('ascii'))
    time.sleep(3)
    output = tn.read_very_eager().decode('ascii')
    print("Output of the 'display ont info by-sn' command:")
    print(output)
    tn.write("Q")
    slot_value = input("Enter the SLOT field value: ")
    pon_value = input("Enter the PON field value: ")
    onu_value2 = input("Enter the ONU ID field value: ")

    tn.write(f"display service-port port 0/{slot_value}/{pon_value} ont {onu_value2}\n".encode('ascii'))
    tn.write("\n")
    time.sleep(3)
    output = tn.read_very_eager().decode('ascii')
    print("Output of the 'display service-port port 0/{slot_value}/{pon_value} ont {onu_value2}' command:")
    print(output)

    id_undo_values = input("Enter the UNDO ID field values separated by commas (e.g., 1,2,3,4): ").split(',')
    for id_undo_value in id_undo_values:
        tn.write(f"undo service-port {id_undo_value.strip()}\n".encode('ascii'))
        time.sleep(1)
        tn.write("\n")

    execute_command(tn, f"interface gpon 0/{slot_value}")
    execute_command(tn, f"ont delete {pon_value} {onu_value2}\n")
    execute_command(tn, "quit")
    # Save the configuration
    save_configuration(tn)

def main():
    host = "IP-Address"
    port = "23"
    username = "root"
    password = "password"

    while True:
        action = input("Do you want to add or delete an ONT? (add/delete/exit): ").strip().lower()
        if action == "exit":
            break
        tn = login_to_olt(host, port, username, password)
        if action == "add":
            add_ont(tn)
        elif action == "delete":
            delete_ont(tn)
        else:
            print("Invalid option. Please enter 'add' or 'delete'.")
        tn.close()

if __name__ == "__main__":
    main()