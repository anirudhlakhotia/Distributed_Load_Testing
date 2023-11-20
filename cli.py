import requests
from print import PrintStyles, print_header, print_success, print_warning, print_error

# Orchestrator node endpoint
orchestrator_url = "http://localhost:5001"

def configure_test():
    print_header("Configure Test")
    
    # Accept user inputs for test configuration
    test_type = input(f"{PrintStyles.OKBLUE}Enter test type (AVALANCHE/TSUNAMI): {PrintStyles.ENDC}")
    message_count_per_driver = int(input(f"{PrintStyles.OKBLUE}Enter message count per driver: {PrintStyles.ENDC}"))
    test_message_delay = float(input(f"{PrintStyles.OKBLUE}Enter test message delay (in seconds): {PrintStyles.ENDC}"))

    # Prepare test configuration data
    test_config = {
        "test_type": test_type,
        "message_count_per_driver": message_count_per_driver,
        "test_message_delay": test_message_delay,
    }

    # Send test configuration to orchestrator
    response = requests.post(f"{orchestrator_url}/test/control", json=test_config)

    if response.status_code == 200:
        print_success("Test configuration sent successfully!")
    else:
        print_error(f"Failed to send test configuration. Status code: {response.status_code}")

def trigger_test():
    # Trigger the test on the orchestrator
    response = requests.post(f"{orchestrator_url}/test/trigger")

    if response.status_code == 200:
        print_success("Test triggered successfully!")
    else:
        print_error(f"Failed to trigger test. Status code: {response.status_code}")

def view_test_progress():
    # View test progress on the orchestrator
    response = requests.get(f"{orchestrator_url}/test/progress")

    if response.status_code == 200:
        status_data = response.json()
        print(f"Test status: {status_data['status']}")
        if status_data['status'] == 'in_progress':
            print(f"Current Test ID: {status_data['test_id']}")
    else:
        print_error(f"Failed to retrieve test progress. Status code: {response.status_code}")

if __name__ == "__main__":
    while True:
        print("\nOptions:")
        print("1. Configure Test")
        print("2. Trigger Test")
        print("3. View Test Progress")
        print("4. Exit")
        
        choice = input("Enter your choice (1/2/3/4): ")

        if choice == "1":
            configure_test()
        elif choice == "2":
            trigger_test()
        elif choice == "3":
            view_test_progress()
        elif choice == "4":
            print("Exiting the CLI.")
            break
        else:
            print_warning("Invalid choice. Please enter a valid option.")
