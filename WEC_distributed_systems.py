import os.path
import random
import shutil
import threading
import time

num_clients = int(input("how many clients?- "))
ops = int(input(f"how many operations? (minimum {num_clients})- "))


class Client:
    operation_ID = 0

    working_dir = os.getcwd()

    clients = []
    lock = threading.Lock()
    # Static variable to store the log file
    log_file = "client_log.txt"

    # Class variable to keep track of the last assigned client ID
    last_assigned_client_id = -1

    number_of_clients = num_clients
    num_ops = ops
    # Static variable for the vector clock
    vector_clocks = {f"Client-{i}": [0 for j in range(num_clients)] for i in
                     range(num_clients)}  # Initialize the vector clock dictionary

    def __init__(self, file_name):
        self.client_id = Client.get_next_client_id()
        self.file_name = os.path.join(Client.working_dir, "Client_files", file_name)
        self.client_thread = threading.Thread(target=self.run_client, name=f"Client-{self.client_id}")
        Client.clients.append(self)

        # Ensure the "Client_files" directory exists
        client_files_directory = os.path.join(Client.working_dir, "Client_files")
        if not os.path.exists(client_files_directory):
            os.makedirs(client_files_directory)

    @classmethod
    def get_next_client_id(cls):
        if cls.last_assigned_client_id < cls.number_of_clients:
            cls.last_assigned_client_id += 1
            return cls.last_assigned_client_id
        else:
            print("number of clients exceeded specified number")
            raise ValueError

    def start(self):
        self.client_thread.start()

    def run_client(self):
        operations = ["read", "write", "update"]
        while True:
            if Client.operation_ID <= Client.num_ops - Client.number_of_clients:
                sleep_time = random.uniform(5, 10)
                time.sleep(sleep_time)

                operator = random.choice(operations)
                match operator:
                    case "read":
                        self.client_read()
                    case "write":
                        self.client_write(f"Performing write from client-{self.client_id}\n")
                    case "update":
                        self.client_update(f"Performing update from client-{self.client_id}\n")
                Client.operation_ID += 1

            else:
                break

    def client_read(self):
        OPERATION = "read"
        """
        read the data and print it on the console
        :return:
        """
        self.update_vector_clock(OPERATION)
        try:
            with open(self.file_name, "r") as file:
                with open(Client.log_file, "a") as file2:
                    file2.write(f"File snapshot saved at {self.file_snapshot(OPERATION)}\n\n")
                print(f"Reading from {os.path.basename(self.file_name)}, content is: ")
                print(file.read())
        except FileNotFoundError:
            print(f"The file {os.path.basename(self.file_name)} does not exist. Creating a new file.")
            with open(self.file_name, "w") as file:
                pass
            with open(Client.log_file, "a") as file2:
                file2.write(f"File snapshot saved at {self.file_snapshot(OPERATION)}\n\n")

        Client.lock.release()

    def client_write(self, content):
        OPERATION = "write"
        """
        writes a new line into the file
        :return:
        """
        self.update_vector_clock(OPERATION)

        try:
            with open(self.file_name, "a") as file:
                file.write(content)
        except FileNotFoundError:
            print(f"The file {os.path.basename(self.file_name)} does not exist. Creating a new file.")
            with open(self.file_name, "w") as file:
                file.write(content)

        with open(Client.log_file, "a") as file:
            file.write(f"File snapshot saved at {self.file_snapshot(OPERATION)}\n\n")
        print(f"Wrote to {os.path.basename(self.file_name)}, synchronization started")

        self.update_files()
        print("Synchronization ends\n")
        Client.lock.release()

    def client_update(self, content):
        OPERATION = "update"
        """
        Updates the last line of the file and appends a visual proof
        :return:
        """
        self.update_vector_clock(OPERATION)

        try:
            with open(self.file_name, "r") as file:
                lines = file.readlines()
                if lines:
                    last_line = lines[-1]
                    updated_line = last_line.strip() + " --- " + content  # Update the last line with additional content
                    lines[-1] = updated_line
                    with open(self.file_name, "w") as file:
                        file.writelines(lines)
                    print(
                        f"Updated last line in {os.path.basename(self.file_name)} with new information, synchronization started")
                else:
                    print(f"The file {os.path.basename(self.file_name)} is empty. Nothing to update.")
        except FileNotFoundError:
            print(f"The file {os.path.basename(self.file_name)} does not exist. Creating a new file.")
            with open(self.file_name, "w") as file:
                file.write(content)

        with open(Client.log_file, "a") as file:
            file.write(f"File snapshot saved at {self.file_snapshot(OPERATION)}\n\n")

        self.update_files()
        print("Synchronization ends\n")
        Client.lock.release()

    def update_files(self):
        for client in Client.clients:
            if client.file_name != self.file_name:
                shutil.copyfile(self.file_name, client.file_name)
                print(f"updated file {client.client_id} with {self.client_id}")

    def update_vector_clock(self, operation):
        Client.lock.acquire()
        Client.vector_clocks[f"Client-{self.client_id}"][self.client_id] += 1
        self.log(operation)
        for i in range(Client.number_of_clients):
            if i != self.client_id:
                Client.vector_clocks[f"Client-{i}"][self.client_id] += 1

    def log(self, operation):
        with open(Client.log_file, "a") as file:
            file.write(
                f"Performed operation - {operation.upper()} on {os.path.basename(self.file_name)} from client - {self.client_id}\n")
            file.write(f'Network time- {time.strftime("%H:%M:%S")}\n')
            file.write(f"Operation ID- {Client.operation_ID}\n")
            file.write("Vector clocks- \n")
            # Write each key-value pair in a new line
            for key, value in Client.vector_clocks.items():
                file.write(f"{key}: {value}\n")

    def file_snapshot(self, operation):
        # print(f"Initializing Snapshot for {operation} from Client-{self.client_id}")
        filename = f"Event-{Client.operation_ID}-Client-{self.client_id}-{operation}.txt"
        with open(filename, "w") as file:
            pass
        snapshots_directory = os.path.join(Client.working_dir, "Snapshots")
        if not os.path.exists(snapshots_directory):
            os.makedirs(snapshots_directory)
        shutil.copyfile(self.file_name, filename)
        shutil.move(filename, os.path.join(Client.working_dir, snapshots_directory))
        # print("Snapshot saved")
        return os.path.join(Client.working_dir, snapshots_directory, filename)


if __name__ == "__main__":

    # Create three clients with unique file names
    clients = [Client(f"File{i}.txt") for i in range(num_clients)]
    for client in clients:
        client.start()

    # Wait for all client threads to finish
    for client in clients:
        client.client_thread.join()

    # Access the vector clock
    print("Vector Clocks:")
    print(Client.vector_clocks)
