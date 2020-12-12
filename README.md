Deploy:

    # dev machine
    git push share master

    # deploy machine
    git pull share master

    . .venv/bin/activate
    pip install -r requirements.txt
    python manager.py migrate
    deactivate

    sudo systemctl restart cmt_manager.service
    sudo systemctl status cmt_manager.service