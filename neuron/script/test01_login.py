from api.api import login, change_password
import pytest
import time
import os
import shutil
from pathlib import Path
import json
import subprocess
import config
from data.error_codes import *
from config import NEURON_PATH

@pytest.fixture(autouse=True)
def setup_and_teardown_neuron():

    start_dir = os.getcwd()
    os.chdir(NEURON_PATH)
    neuron_path = "./neuron"
    command_neuron = [neuron_path]
    process_neuron = subprocess.Popen(command_neuron, stderr=subprocess.PIPE)
    time.sleep(1)
    os.chdir(start_dir)
    assert process_neuron.poll() is None

    yield
        
    os.chdir(NEURON_PATH)
    process_neuron.kill()
    time.sleep(1)
    _, err = process_neuron.communicate()
    os.chdir(start_dir)
    assert process_neuron.poll() is not None, "Neuron process didn't stop"
    assert err.decode() == '', "stderr not empty: " + err.decode()

@pytest.fixture(scope="session", autouse=True)
def move_and_delete_logs():
    yield
    
    start_dir = os.getcwd()
    report_directory = "report"
    Path(report_directory).mkdir(exist_ok=True)
    os.chdir(NEURON_PATH)
    if os.path.exists("./logs/neuron.log"):
        shutil.copy2("./logs/neuron.log", f"{start_dir}/{report_directory}/test01_login_neuron.log")
        os.remove("./logs/neuron.log")
    os.chdir(start_dir)

class TestLogin:

    with open('data/test01_login_data.json') as f:
        test_data = json.load(f)

    def test01_login_success(self, setup_and_teardown_neuron):
        print("---given:name and password, when:login, then:success with token---")
        test_data = TestLogin.test_data
        user_data = test_data['correct_user_data']

        response = login(test_data=user_data)
        assert 200 == response.status_code
        print(response.json())
        config.TOKEN = response.json().get("token")
    
    def test02_login_invalid_user_fail(self, setup_and_teardown_neuron):
        print("---given:invalid user name, when:login, then:login failed and return error---")
        test_data = TestLogin.test_data
        user_data = test_data['invalid_user']

        response = login(test_data=user_data)
        assert 401 == response.status_code
        assert NEU_ERR_INVALID_USER == response.json().get("error")

    def test03_login_invalid_password_fail(self, setup_and_teardown_neuron):
        print("---given:invalid password, when:login, then:login failed and return error---")
        test_data = TestLogin.test_data
        user_data = test_data['invalid_password']

        response = login(test_data=user_data)
        assert 401 == response.status_code
        assert NEU_ERR_INVALID_PASSWORD == response.json().get("error")
    
    def test04_login_change_password_success(self, setup_and_teardown_neuron):
        print("---given:name, old and new password, when:login, then:success---")
        test_data = TestLogin.test_data
        user_data1 = test_data['change_password1']
        headers = {
            "Authorization": f"Bearer {config.TOKEN}"
        }
        config.headers = headers
        response = change_password(test_data=user_data1, header_data=headers)
        assert 200 == response.status_code
        assert NEU_ERR_SUCCESS == response.json().get("error")

        user_data2 = test_data['change_password2']
        response = change_password(test_data=user_data2, header_data=headers)
        assert 200 == response.status_code
        assert NEU_ERR_SUCCESS == response.json().get("error")
    