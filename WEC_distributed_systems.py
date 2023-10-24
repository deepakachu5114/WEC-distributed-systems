import os.path
import random
import shutil
import threading
import time

num_clients = int(input("How many clients in the system?- "))
ops = int(input(f"How many operations in total? (minimum {num_clients})- "))


class Client:
    operation_ID = 0
    working_dir = os.getcwd()
    clients = []
    lock = threading.Lock()

    # Static variable to store the log file
    log_file = "Client_log.txt"

    # Class variable to keep track of the last assigned client ID
    last_assigned_client_id = -1

    # number of clients in the distributed system
    number_of_clients = num_clients

    # total number of operations
    num_ops = ops

    # Static variable for the vector clock
    vector_clocks = {f"Client-{i}": [0 for j in range(num_clients)] for i in
                     range(num_clients)}  # Initialize the vector clock dictionary

    def __init__(self, file_name):
        self.client_id = Client.get_next_client_id()
        self.file_name = os.path.join(Client.working_dir, "Client_files", file_name)
        self.client_thread = threading.Thread(target=self.run_client, name=f"Client-{self.client_id}")
        Client.clients.append(self)

        client_files_directory = os.path.join(Client.working_dir, "Client_files")
        if not os.path.exists(client_files_directory):
            os.makedirs(client_files_directory)

    @classmethod
    def get_next_client_id(cls):
        """
        Automatically gets the next client ID since the variable is static
        :raises: Value error if the number of clients is less than -1
        :return: new client ID
        """
        if cls.last_assigned_client_id < cls.number_of_clients:
            cls.last_assigned_client_id += 1
            return cls.last_assigned_client_id
        else:
            print("Number of clients can't be the specified number")
            raise ValueError

    def start(self):
        """
        starts the client thread
        :return:
        """
        self.client_thread.start()

    def run_client(self):
        """
        Most important function here.
        Chooses an operation at random and then calls the corresponding functions.
        While the number of total operations hasn't exceeded the given limit,
        a thread will RANDOMLY SLEEP FOR 5-10 SECONDS BEFORE EVERY OPERATION TO SIMULATE REAL WORLD LATENCY
        :return:
        """
        operations = ["read", "write", "update"]
        while True:
            if Client.operation_ID <= Client.num_ops - Client.number_of_clients:
                # PUT THE THREAD TO SLEEP FOR A RANDOM TIME INTERVAL TO SIMULATE LATENCY
                sleep_time = random.uniform(5, 10)
                time.sleep(sleep_time)
                # RANDOM CHOICE OF OPERATIONS
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
        writes a new line into the client file
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
        Updates the last line of the client file with new information
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
        """
        Synchronise all the files.
        eg:
        if there is a new write operation on file1, then after performing it, the latest file is copied to all
        other client's files.
        :return:
        """
        for client in Client.clients:
            if client.file_name != self.file_name:
                shutil.copyfile(self.file_name, client.file_name)
                print(f"updated file {client.client_id} with {self.client_id}")

    def update_vector_clock(self, operation):
        """
        Update the vector clock of each client after every operation
        :param operation:
        :return:
        """
        Client.lock.acquire()
        Client.vector_clocks[f"Client-{self.client_id}"][self.client_id] += 1
        self.log(operation)
        for i in range(Client.number_of_clients):
            if i != self.client_id:
                Client.vector_clocks[f"Client-{i}"][self.client_id] += 1

    def log(self, operation):
        """
        Log the operations with details like the thread performing it, vector clock, network timestamp, snapshot, operation ID
        :param operation: to log the operation type in the log file
        :return:
        """
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
        """
        Takes a snapshot of the client's file.
        eg:
        if a file was updated, before any further changes are made, a copy of the file with operation ID, thread name,
        operation type is made which has the exact same data as the client's file at that moment.
        :param operation:
        :return:
        """
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

    clients = [Client(f"File{i}.txt") for i in range(num_clients)]
    for client in clients:
        client.start()

    # Wait for all client threads to finish
    for client in clients:
        client.client_thread.join()

    # Access the vector clock
    print(f"Successfully executed {ops} operations in a system of {num_clients} processes")
    print(f"Client files stored at {os.path.join(Client.working_dir, 'Client_files')}")
    print(f"Snapshots stored at {os.path.join(Client.working_dir, 'Snapshots')}")
    print(f"Log file stored at {os.path.join(Client.working_dir, 'Client_log.txt')}")
