# Gradient AI Benchmarking 

The following directory aims to provide a testing framework to perform online inference benchmarks. 


# Prerequisites
- You need to have created a huggingface account and an access token
- Depending on the model you are benchmarking some of them require explicit access. You will need to request this access


# Initial setup

## Access to test bench
TODO: this can be a public repo so we can just clone it
At the moment this is a private repo so we will need to manually upload this to the GPU droplet

run the following commands
```
zip -r testbench.zip testbench
scp testbench.zip root@<dropletIP>:
```

ssh into the droplet and 
```
sudo apt install unzip
unzip testbench.zip
```

## Set up droplet environment
Check if docker is installed (it is on nvidia systems not on AMD)

```
docker ps -a # this will fail if docker isnt installed
```

Add Your User to Docker Group
By default, you need sudo to run Docker commands.
# Add your current user to the docker group
sudo usermod -aG docker $USER

# Apply the group changes (choose one of these options):

# Option 1: Log out and log back in via SSH
# Just disconnect and reconnect your SSH session

# Option 2: Or run this command to apply changes immediately
newgrp docker

Start Docker Service
Make sure Docker is running
# Start Docker service
sudo systemctl start docker

# Enable Docker to start automatically when system boots (optional)
sudo systemctl enable docker

# Check if Docker is running
sudo systemctl status docker


If docker is already installed skip this step
```
curl -fsSL https://get.docker.com | sudo sh
make start_docker_daemon
```

make all the sh scripts executable
```
make make_exec_scripts
```

open a separate shell (one will be for the client one will be for the server)

## Server setup
Run one of the server config setups under /test-parameters/server-config
- This will start the docker container serving the model specified in the config

Make sure you update your huggingface token in the .sh file you are running 

## Run the corresponding server setup that you wish to test

You will need to modify the server parameters as required in the *docker.sh file as required by the test
```
cd test-parameters/server_config/vllm

./server-amd-<model>-docker.sh
./server-nvidia-<model>-docker.sh
```

## Client setup

Run the following for Nvidia systems
```
docker build -f Dockerfile.nvidia -t vllm-env-do-infra-nvidia .

# Make sure you run this form root / same level as testbench directory
git clone https://github.com/vllm-project/vllm.git

docker run -it --rm \
  --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --ipc=host \
  -v /root/testbench:/root/testbench \
  -v /root/vllm:/root/vllm \
  vllm-env-do-infra-nvidia
```

Run the following for AMD systems
```
docker build -f Dockerfile.amd -t vllm-env-do-infra-amd .

git clone https://github.com/vllm-project/vllm.git

docker run -it --rm \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --ipc=host \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  -v /root/testbench:/root/testbench \
  -v /root/vllm:/root/vllm \
  vllm-env-do-infra-amd

```


## Run the benchmark
Before kicking off the benchmark from the client side make sure the docker container is running

```
docker ps -a
docker logs <containerId>
```

you should see something like

```
...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

```

**Please note that you will need to update the endpoint IP address to match that of your Droplet IP in the *benchmark_config* files used in the test run.**

Run the following from inside the docker container
```


```
chmod +x testbench/

# Examples
nohup python3 run_benchmark.py test-parameters/client_config/vllm/benchmark_config_mistral_test_short.yaml nvidia > output.log 2>&1 &

nohup python run_benchmark.py test-parameters/client_config/vllm/benchmark_config_mistral_test_short.yaml amd > output.log 2>&1 &

nohup python run_benchmark_test2.py test-parameters/client_config/vllm/benchmark_config_deepseek_test2.yaml amd > output.log 2>&1 &
```

```
ps aux | grep python
# or check the specific PID
ps -p 4262

tail -f output.log

ls -la output.log
cat output.log

kill 4262

## Download the results
- Create a folder for the results you wish to download
- cd into that folder


```
scp root@<dropletIP>:testbench/vllm/benchmark_results.zip .
unzip benchmark_results.zip