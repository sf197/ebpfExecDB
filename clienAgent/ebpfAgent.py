#!/usr/bin/env python3

from bcc import BPF
from pymongo import MongoClient
import time
import os
import logging

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "execMcpSecurity"
COLLECTION_NAME = "commands"

# Logging configuration
LOG_FILE = "/var/log/command.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# eBPF program
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct data_t {
    char comm[TASK_COMM_LEN];
    char argv[256];
};

BPF_PERF_OUTPUT(events);

int syscall__execve(struct pt_regs *ctx, const char __user *filename,
                    const char __user *const __user *argv,
                    const char __user *const __user *envp) {
    struct data_t data = {};
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    bpf_probe_read_user_str(&data.argv, sizeof(data.argv), (void *)argv[0]);
    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
"""

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def handle_event(cpu, data, size):
    event = b["events"].event(data)
    command = event.comm.decode('utf-8')
    args = event.argv.decode('utf-8')
    
    # Log to file
    log_message = f"Command: {command}, Args: {args}"
    logging.info(log_message)
    
    # Insert to MongoDB
    document = {
        "timestamp": time.time(),
        "command": command,
        "arguments": args
    }
    collection.insert_one(document)

# Load BPF program
b = BPF(text=bpf_text)
# 修改事件名为 __x64_sys_execve（x86_64 架构）
b.attach_kprobe(event="__x64_sys_execve", fn_name="syscall__execve")

print("Monitoring system commands... Press Ctrl+C to stop.")

# Process events
b["events"].open_perf_buffer(handle_event)
while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        break

