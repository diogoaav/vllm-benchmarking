.PHONY: make_exec_scripts setup_env setup_benchmark setup_docker_daemon

make_exec_scripts:
	chmod +x *.sh
	chmod +x test-parameters/server_config/modular_max/*.sh	
	chmod +x test-parameters/server_config/vllm/*.sh

setup_env:
	./environment_setup.sh

start_docker_daemon:
	sudo systemctl start docker

setup_benchmark:
	@bash -c '\
		source ~/.bashrc && \
		pyenv install -s 3.11.13 && \
		pyenv global 3.11.13 && \
		python -m venv myenv && \
		source myenv/bin/activate && \
		git clone https://github.com/vllm-project/vllm.git && \
		cd vllm/benchmarks && \
		pip install pandas datasets transformers pillow vllm \
	'
