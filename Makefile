# =====================================================
# Environment & Security Commands
# =====================================================
.PHONY: env-encrypt env-decrypt env-check api-key-check
env-encrypt: ## Encrypt .env file with AES-256
	@if [ ! -f .env ]; then echo "$(RED)Error: .env file not found$(NC)"; exit 1; fi
	@echo "$(BLUE)Encrypting .env file...$(NC)"
	openssl aes-256-cbc -a -salt -pbkdf2 -in .env -out .env.enc
	@echo "$(GREEN).env file encrypted as .env.enc$(NC)"

env-decrypt: ## Decrypt .env.enc file
	@if [ ! -f .env.enc ]; then echo "$(RED)Error: .env.enc file not found$(NC)"; exit 1; fi
	@echo "$(BLUE)Decrypting .env file...$(NC)"
	openssl aes-256-cbc -d -a -pbkdf2 -in .env.enc -out .env
	@echo "$(GREEN).env file decrypted$(NC)"