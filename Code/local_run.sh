#! /bin/sh

echo "-----------------------------------------------------------------"
echo "This will start a local run of the project."
echo "-----------------------------------------------------------------"
read -p "Would you like to continue? (y/n): " choice

if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    if [[ -d ".venv" ]]; then
        echo "Enabling the local environment..."
        . .venv/bin/activate
        export ENV=development
        python3 app.py
        deactivate
        

    else
        echo "Local environment isn't set up yet. Try running 'local_setup.sh' first !!"
        
    fi

elif [[ "$choice" == "n" || "$choice" == "N" ]]; then
    echo "No worries. Exiting..."

else
    echo "Invalid choice. So exiting..."

fi
