import time
import random

while True:
    print("\nWelcome to Rick's Typing Speed Tester\n")
    
    print("1 - Choose a random sentence")
    print("2 - Create your own sentence")
    
    while True:
        choice = input("Enter your choice: ")
        
        if choice == "1":
            sentences = [
                "Python is a programming language that lets you work more quickly and integrate your systems more effectively.",
                "You can learn to use Python and see almost immediate gains in productivity and lower maintenance costs.",
                "Python is used successfully in thousands of real-world business applications around the world, including many large and mission-critical systems.",
                "Python has been an important part of Google since the beginning and remains so as the system grows and evolves."
            ]
            sentence = random.choice(sentences)
            break
        
        elif choice == "2":
            sentence = input("Enter your sentence here:\n>> ")
            break
        
        else:
            print("Invalid input. Please try again!")

    input("\nPress Enter to start the speed test.")
    
    print("\nType the following sentence:\n")
    print(sentence)
    
    start = time.time()
    write = input(">> ")
    end = time.time()

    time_taken = max(end - start, 0.01)  # Prevent division by zero
    minutes = time_taken / 60

    count = sum(1 for i in range(min(len(sentence), len(write))) if sentence[i] == write[i])

    cpm = count / minutes
    wpm = cpm / 4.5  # Assume each word is approximately 4.5 letters
    accuracy = (count / len(sentence)) * 100

    print("\nResults:")
    print(f"CPM: {cpm:.2f}")
    print(f"WPM: {wpm:.2f}")
    print(f"Accuracy: {accuracy:.2f}%")

    print("\nDo you want to test again?")
    print("1 - Yes")
    print("2 - Exit")

    retry_choice = input("Enter your choice: ")
    if retry_choice != "1":
        print("Goodbye!")
        break