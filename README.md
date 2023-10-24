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
### This section explains what the program does on the whole, we will explore the nitty gritties in sections after this

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





