# WEC-distributed-systems
Task submission for WEC systems recruitment

Deepak C Nayak 
Sophomore, AI

## How to run the file
The .py file is self-sufficient and has no dependencies that need to be installed.
Run the Python file (preferably on an IDE) and follow these steps:
- When prompted to enter the number of clients, enter any number of your choice. The code will create those many clients to be part of the distributed system.
- When prompted to enter the TOTAL number of operations, again enter any number BIGGER than the number of clients to ensure smooth running of the program.

## Brief overview 
### This section provides an overview of the program's functionality as a whole. We will delve into the finer details in subsequent sections.

Every `client` is an instance of the `CLient` class, each `client` has a corresponding _file_ and a _thread_, and other attributes.
A `client` thread will make changes into the client's corresponding file through the function `run_client`.
The `run_client` function will account for real world latency by putting the operating thread to sleep for a random time interval.
Then the function will randomly choose one of _write_, _read_ or _update_ operations, that is to be performed on the client's file and makes appropriate function calls.

All the 3 functions (read/write/update) do the following:
1. Update the client's vector clock.
2. Log the operation along with the client ID, Network timestamp, and the newly updated vector clock to the `Client_log.txt` file.
3. Once the logging is done, perform the operation on the client's file.
4. After performing the operation, a snapshot of the file is taken by invoking `file_snapshot` function.
5. Synchronise all other files in the system to be up-to-date with the last operation by invoking `update_files` function.

All the steps above are performed by the thread while having acquired a lock at step 1 and releasing it after step 5.
This lock is the reason why we do not need to explicitly have a mechanism to rule out causal anomalies, the lock makes sure that the events are casually consistent.

---
NOTE: THE CONTENT BELOW WAS ADDED AFTER THE DEADLINE, FOR MORE CLARITY. THE CODE HASN'T BEEN MODIFIED IN ANY WAY.
---


## Code flow and how the code maintains causal consistency
### Here we will take a deeper look at how the code works and is designed to maintain causal consistency

Let us imagine we have 3 Clients - `client1`, `client2` and `client3`

Let the operations be as follows:
`client1` updates their file - `U`
`client2` writes in their file - `W`
`client3` reads their file - `R`
and let the order be (for simplicity) `W`, `U`, `R`

Here is the overall process:

We will refer to the lock as `L` and the threads as `T1`, `T2`, `T3` corresponding to the clients in the same order.

1. `T1`, `T2`, `T3` are started
2. `T1` invokes `run_client`
3. `T1` will be put to sleep for a random time interval to simulate real-world latency
4. The same happens with `T2` and `T3` parallelly.
5. Whichever thread wakes up first gets to choose an operation - here we are assuming `T2` woke up first and chose `W`
6. `T2` invokes `client_write`
7. `client_write` invokes `update_vector_clock`
8. Once the thread has reached `update_vector_clock`, it acquires `L`, a static attribute of class `CLient`.
  - This means no other thread now can enter `update vector clock`.
  - `T1` and `T3` (in that order) will also invoke `client_update` and `client_read` respectively and those in turn will invoke `update_vector_clock`
  - But since `T2` has acquired the lock, `T1` and `T3` will be queued until the `L` has been released.

9. `update_vector_clock` updates the vector clock dictionary (again a static variable) and calls the `log` function
10. `log` logs the operation in `Client_log.txt` with all necessary data like the client performing it, time stamp, network time, the kind of operation, and the operation ID.
11.  Now after logging the operation, the thread `T2` returns back to `client_write`. The function creates the file (since it doesn't exist yet) and writes data into it.
12.  `client_write` will now invoke `file_snapshot` to save the state of the client's file at this point in time.
13.  `file_snapshot` will make a copy of the client's file at that point in time, name it as `EVENT_ID-CLIENT_ID-OPERATION_TYPE.txt` and save it in a separate directory.
14.  `Client_log.txt` will be updated to have the path of the corresponding file snapshot.
15.  After this, `client_write` invokes `update_files`. This is to synchronize all the other client files in the system to be up-to-date with the changes the client made to their file.
16.  `update_files` scans for all the client files other than the client performing the operation, and updates them with the content from the operating client's file.
17.  And now, `T2` releases `L`, allowing other threads in the queue to perform their activities. 

After the lock has been released, the next thread in the queue (`T1`) will acquire it and repeat the process above (steps 7 - 17) with its respective operation.
This process goes on until a certain number of operations (in total) are completed. This number is specified at the beginning of the program by the user.

   

