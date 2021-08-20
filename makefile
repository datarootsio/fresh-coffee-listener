.DEFAULT_GOAL := help

# TODO: Fill the variables based on your audio path / office name / PostgreSQL parameters
export COFFEE_AUDIO_PATH=/home/pi/coffee-machine-monitoring/sounds/coffee-sound.m4a
export SD_DEFAULT_DEVICE=2
export OFFICE_NAME=leuven
export DB_USER=
export DB_PASSWORD=
export DB_HOST=
export DB_PORT=
export DB_NAME=
export DB_TABLE=

###############################################################
# COMMANDS                                                    #
###############################################################
install: ## installing dependencies for ARM architectures for all x86 architectures
	@echo ">>> installing dependencies for x86 architectures"
	pip install -r requirements.txt

install-arm: ## installing dependencies for ARM architectures like Raspberry Pi
	@echo ">>> installing dependencies for ARM architectures like Raspberry Pi"
	sudo apt install -y libatlas-base-dev. libportaudio2 llvm-9 libpq5
	LLVM_CONFIG=llvm-config-9 pip install llvmlite
	pip install -r requirements.txt

run: ## Start listening the environment to detect coffee sound
	@echo ">>> generating features"
	python3 detect_sound.py

run-systemctl: ## Start listening the environment with systemctl (auto-restart if fails)
	@echo ">>> generating features"
	sudo cp coffee_machine_service.service /etc/systemd/system/coffee_machine_service.service
	sudo cp coffee_machine_service.timer /etc/systemd/system/coffee_machine_service.timer
	sudo systemctl enable coffee_machine_service.service
	sudo systemctl enable coffee_machine_service.timer
	sudo systemctl daemon-reload
	sudo systemctl restart coffee_machine_service.timer
