#!/bin/bash
# Helper script to add your API keys to all shell scripts for local development

read -p "Enter your OpenAI API key (or press Enter to skip): " openai_key
read -p "Enter your Anthropic API key (or press Enter to skip): " anthropic_key

for script in run_gpt*.sh run_judge*.sh run_remaining*.sh; do
    if [ -f "$script" ] && [ -n "$openai_key" ]; then
        # Replace placeholder or add after set -e
        if grep -q "# export OPENAI_API_KEY=" "$script"; then
            sed -i "s|# export OPENAI_API_KEY=.*|export OPENAI_API_KEY=$openai_key|" "$script"
        elif ! grep -q "export OPENAI_API_KEY=" "$script"; then
            sed -i "s|^set -e$|set -e\nexport OPENAI_API_KEY=$openai_key|" "$script"
        fi
        echo "Updated: $script"
    fi
done

for script in run_claude*.sh; do
    if [ -f "$script" ] && [ -n "$anthropic_key" ]; then
        # Replace placeholder or add after set -e
        if grep -q "# export ANTHROPIC_API_KEY=" "$script"; then
            sed -i "s|# export ANTHROPIC_API_KEY=.*|export ANTHROPIC_API_KEY=$anthropic_key|" "$script"
        elif ! grep -q "export ANTHROPIC_API_KEY=" "$script"; then
            sed -i "s|^set -e$|set -e\nexport ANTHROPIC_API_KEY=$anthropic_key|" "$script"
        fi
        echo "Updated: $script"
    fi
done

echo "Done! API keys added to scripts for local use."
echo "Note: These will be automatically removed when you commit to Git."
