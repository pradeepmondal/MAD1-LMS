#! /bin/sh

echo "-----------------------------------------------------------------"
echo "This will setup the local environment for the project."
echo "-----------------------------------------------------------------"
read -p "Would you like to continue? (y/n): " choice

if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    echo "Setting up the local environment..."
    if [[ -d ".venv" ]]; then
        echo ".venv folder already exists, proceeding further..."
    else
        echo "creating .venv folder and installing the dependencies..."
        python3 -m venv .venv
    fi
    . .venv/bin/activate

    pip install --upgrade pip
    pip install -r requirements.txt

    deactivate

elif [[ "$choice" == "n" || "$choice" == "N" ]]; then
    echo "You chose no. So exiting..."
else
    echo "Invalid choice. So exiting..."
fi