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


# Function to process a single JSON file
def process_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"Skipping {file_path}: Error reading JSON - {e}")
        return None  # Skip this file if there's an error

    # Extract first number from input_lens and output_lens if available
    input_lens = data.get("input_lens", [])
    output_lens = data.get("output_lens", [])

    return {
        "model_id": data.get("model_id", "Unknown"),
        "input_lens_first": input_lens[0] if input_lens else None,
        "output_lens_first": output_lens[0] if output_lens else None,
        "num_prompts": data.get("num_prompts", 0),
        "Concurrency": data.get("max_concurrency", "Unknown"),
        "request_throughput": data.get("request_throughput", "N/A"),
        "output_throughput": data.get("output_throughput", "N/A"),
        "total_token_throughput": data.get("total_token_throughput", "N/A"),
        "mean_ttft_ms": data.get("mean_ttft_ms", "N/A"),
        "median_ttft_ms": data.get("median_ttft_ms", "N/A"),
        "p99_ttft_ms": data.get("p99_ttft_ms", "N/A"),
        "mean_tpot_ms": data.get("mean_tpot_ms", "N/A"),
        "median_tpot_ms": data.get("median_tpot_ms", "N/A"),
        "p99_tpot_ms": data.get("p99_tpot_ms", "N/A"),
        "mean_itl_ms": data.get("mean_itl_ms", "N/A"),
        "median_itl_ms": data.get("median_itl_ms", "N/A"),
        "p99_itl_ms": data.get("p99_itl_ms", "N/A"),
        "duration": data.get("duration", "N/A"),
    }

# Function to process all JSON files in the current directory
def process_json_files(output_csv):
    results = []
    processed_files = 0
    skipped_files = 0

    # Gather all JSON files in the current directory with their full path
    json_files = [
        os.path.join(".", f)
        for f in os.listdir(".")
        if f.endswith('.json') and os.path.isfile(f)
    ]

    # Sort the files by last modified time (oldest to newest)
    json_files.sort(key=os.path.getmtime)

    for file_path in json_files:
        print(f"Processing: {file_path}")

        result = process_json_file(file_path)
        if result:
            results.append(result)
            processed_files += 1
        else:
            skipped_files += 1

    # Ensure there is data to write
    if not results:
        print("No valid JSON files processed. Exiting without writing CSV.")
        return

    # Write the processed data to a CSV file
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ CSV saved as: {output_csv}")
    print(f"✅ Processed: {processed_files} files")
    print(f"⚠️ Skipped: {skipped_files} files (errors or invalid JSON)")



def build_command_from_config(config):
    cmd = [
        "python", "../vllm/benchmarks/benchmark_serving.py",
        "--backend", config["backend"],
        "--base-url", config["base_url"],
        "--endpoint", config["endpoint"],
        "--model", config["model"],
        "--dataset-name", "random",
        "--num-prompts", str(config["num_prompts"]),
        "--max-concurrency", str(config["concurrency"]),
        "--request-rate", str(config["request_rate"]),
        "--random-input-len", str(config["prompt_length"]),
        "--random-output-len", str(config["output_length"]),
        "--percentile-metrics", "ttft,tpot,itl,e2el",
        "--save-result",
        "--ignore-eos"
    ]
    return cmd

def move_results():
    result_dir = Path("results")
    result_dir.mkdir(exist_ok=True)

    for ext in ["json", "csv"]:
        for file in Path(".").glob(f"*.{ext}"):
            dest = result_dir / file.name
            print(f"📦 Moving {file} → {dest}")
            shutil.move(str(file), str(dest))


def zip_folder(folder_path, output_zip_path):
    folder_path = Path(folder_path).resolve()
    output_zip_path = Path(output_zip_path).with_suffix('.zip')

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, arcname=file_path.relative_to(folder_path))
    print(f"✅ Folder '{folder_path}' zipped as '{output_zip_path}'")

def main(yaml_path, gpu_type):
    PROFILE_SCRIPT = None
    if gpu_type == "amd":
        PROFILE_SCRIPT = "./profile_rocm.sh"
    elif gpu_type == "nvidia":
        PROFILE_SCRIPT = "./profile_nvidia_smi.sh"


    try:
        with open(yaml_path, 'r') as f:
            configs = yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load YAML: {e}")
        sys.exit(1)

    if not isinstance(configs, list):
        print("YAML file must contain a list of configuration dictionaries.")
        sys.exit(1)

    for config in configs:
        cmd = build_command_from_config(config)
        print("▶️ Running command:\n", " ".join(cmd))

        # Create unique log file per run
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = f"rocm_profile_{timestamp}_c{config['concurrency']}_l{config['prompt_length']}.csv"

        try:
            profiler_proc = subprocess.Popen(
                [PROFILE_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**dict(os.environ), "LOGFILE": log_file}
            )
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print("❌ Command failed with exit code", e.returncode)
            sys.exit(e.returncode)
        finally:
            # Kill profiler script after test
            profiler_proc.terminate()
            try:
                profiler_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                profiler_proc.kill()

    output_csv = "./benchmark_summary.csv"  
    process_json_files(output_csv)
    move_results()
    zip_folder("results", "benchmark_results.zip")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_benchmark.py <config.yaml> <gpu_profile_script>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
