import subprocess
import re

f = open("/home/bgardner/workspace/tracer/out.log", "w")

def search(text, regex, default=[]):
    matches = re.search(regex, text)
    if matches is None:
        return default
    groups = matches.groups()
    if len(groups) == 0:
        return default
    return groups


root_pid = None

processes = {}

command = [
    "strace",
    "-v",
    "-s", "1024",
    "-e", "trace=execve,openat",
    "-f",
    "/usr/bin/bash",
    "-c",
    "source build/envsetup.sh && lunch msm8996-userdebug && make bootimage"
]  # "/usr/bin/make", "bootimage"
process = subprocess.Popen(command, stderr=subprocess.PIPE)
x = 0
while True:
    output = process.stderr.readline()
    if len(output) == 0 and process.poll() is not None:
        break
    if output:
        line = output.decode("utf-8").strip()

        run_pid = search(line, r"^\[pid\s*(\d*)\]", -1)

        attach_pid = search(line, r"strace\: Process (\d*) attached")
        if len(attach_pid) == 1:
            root_pid = attach_pid
            # print(f"--- {root_pid}")

        terms = search(line, r"([\w]*)\((.*)\)")
        if len(terms) >= 1:
            func_name = terms[0]
            args = terms[1]
            if func_name == "execve":
                processes[run_pid] = args
            if func_name == "openat":
                args = args.split(", ")
                file = args[1]
                flags = args[2]
                prog = run_pid
                if run_pid in processes:
                    prog = processes[run_pid]
                if "mkbootimg" in prog \
                        or "boot_signer" in prog \
                        or "BootSignature" in prog \
                        or "acp" in prog \
                        or "boot.img" in file \
                        or "Image.gz" in file \
                        or "msm8996/kernel" in file \
                        or "ramdisk.img" in file:
                    if not file.startswith('"/usr') \
                            and "lib64" not in file \
                            and "site-packages" not in file \
                            or "BootSignature" in file \
                            and not file.startswith('"/opt') \
                            and not file.startswith('"/etc') \
                            and not file.startswith('"/lib'):
                        print(f"---=== {prog}\n\topens {file} for {flags}")
        # else:
            # print("--- none")
        f.write(line)
        f.write('\n')
rc = process.poll()

f.close()

