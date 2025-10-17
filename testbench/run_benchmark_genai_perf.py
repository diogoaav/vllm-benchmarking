# run_genaiperf_benchmark.py
import yaml
import subprocess
import sys
import time
import os
import shutil
import json
import csv
import zipfile
from pathlib import Path


# -------------------------------
# JSON parsing for genai-perf
# -------------------------------
def process_json_file(file_path):
    """Parse a single genai-perf JSON output file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"Skipping {file_path}: Error reading JSON - {e}")
        return None

    return {
        "model": data.get("model_id", "Unknown"),
        "num_prompts": data.get("num_prompts", "Unknown"),
        "concurrency": data.get("concurrency", "Unknown"),
        "p50_latency_ms": data.get("latency", {}).get("p50", "N/A"),
        "p90_latency_ms": data.get("latency", {}).get("p90", "N/A"),
        "p99_latency_ms": data.get("latency", {}).get("p99", "N/A"),
        "throughput_rps": data.get("throughput", "N/A"),
        "success_rate": data.get("success_rate", "N/A"),
        "timestamp": data.get("timestamp", "N/A"),
    }


def process_json_files(output_csv):
    """Process all JSON files and combine into a summary CSV."""
    results = []
    processed_files = 0
    skipped_files = 0

    json_files = [
        os.path.join(".", f)
        for f in os.listdir(".")
        if f.endswith(".json") and os.path.isfile(f)
    ]
    json_files.sort(key=os.path.getmtime)

    for file_path in json_files:
        print(f"Processing: {file_path}")
        result = process_json_file(file_path)
        if result:
            results.append(result)
            processed_files += 1
        else:
            skipped_files += 1

    if not results:
        print("No valid JSON files processed. Exiting without writing CSV.")
        return

    with open(output_csv, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ CSV saved as: {output_csv}")
    print(f"✅ Processed: {processed_files} files")
    print(f"⚠️ Skipped: {skipped_files} files")


# -------------------------------
# Command builder for genai-perf
# -------------------------------
def build_command_from_config(config):
    """Build genai-perf command for one config entry."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"genaiperf_result_{timestamp}.json"

    cmd = [
        "genai-perf",
        "--model", config["model"],
        "--service-kind", "openai",
        "--endpoint", "v1/completions",
        "--endpoint-type", "completions",
        "--num-prompts", str(config["num_prompts"]),
        "--concurrency", str(config["concurrency"]),
        "--url", config["base_url"],
        "--json", output_file,
    ]
    return cmd


# -------------------------------
# Results handling
# -------------------------------
def move_results():
    result_dir = Path("results")
    result_dir.mkdir(exist_ok=True)

    for ext in ["json", "csv"]:
        for file in Path(".").glob(f"*.{ext}"):
            if not file.name.startswith("."):
                dest = result_dir / file.name
                print(f"📦 Moving {file} → {dest}")
                shutil.move(str(file), str(dest))


def zip_folder(folder_path, output_zip_path):
    folder_path = Path(folder_path).resolve()
    output_zip_path = Path(output_zip_path).with_suffix(".zip")

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, arcname=file_path.relative_to(folder_path))

    print(f"✅ Folder '{folder_path}' zipped as '{output_zip_path}'")


# -------------------------------
# Main loop
# -------------------------------
def main(yaml_path, gpu_type):
    PROFILE_SCRIPT = None
    if gpu_type == "amd":
        PROFILE_SCRIPT = "./profile_rocm.sh"
    elif gpu_type == "nvidia":
        PROFILE_SCRIPT = "./profile_nvidia_smi.sh"

    try:
        with open(yaml_path, "r") as f:
            configs = yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load YAML: {e}")
        sys.exit(1)

    if not isinstance(configs, list):
        print("YAML file must contain a list of configuration dictionaries.")
        sys.exit(1)

    for i, config in enumerate(configs, 1):
        print(f"\n{'='*50}")
        print(f" Running config {i}/{len(configs)}")
        print(f" Model: {config.get('model')}")
        print(f" Concurrency: {config.get('concurrency')}")
        print(f" Num prompts: {config.get('num_prompts')}")
        print(f"{'='*50}")

        cmd = build_command_from_config(config)
        print("▶️ Running command:\n", " ".join(cmd))

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = f"gpu_profile_{timestamp}_c{config['concurrency']}.csv"

        try:
            profiler_proc = None
            if PROFILE_SCRIPT and os.path.exists(PROFILE_SCRIPT):
                profiler_proc = subprocess.Popen(
                    [PROFILE_SCRIPT],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env={**dict(os.environ), "LOGFILE": log_file},
                )

            subprocess.run(cmd, check=True)

        except subprocess.CalledProcessError as e:
            print("❌ Command failed with exit code", e.returncode)
            sys.exit(e.returncode)
        finally:
            if profiler_proc:
                profiler_proc.terminate()
                try:
                    profiler_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    profiler_proc.kill()

        print("⏳ Cooling down (10s)...")
        time.sleep(10)

    output_csv = "./genaiperf_summary.csv"
    process_json_files(output_csv)
    move_results()
    zip_folder("results", "genaiperf_results")

    print("\n✅ Benchmark suite completed!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_genaiperf_benchmark.py <config.yaml> <gpu_type>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
